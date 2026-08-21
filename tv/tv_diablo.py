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
#   ONE logical AI path (scout secondary is DEAD forever):
#     settle / queue / heartbeat → dual-lane (OCR flash + Claude deep).
#   v863+ READER POOL: up to TV_POOL concurrent warm Claude workers with capture-order
#   apply (not a second freestyle scout engine). Film is high-FPS HD; ON AIR status is a
#   tiny chip. OFF/STOP seal session_end into sessions.jsonl. Claude deep is multi-second
#   by nature — OCR chips + smooth film are the live-drive feel.
# ═══════════════════════════════════════════════════════════════════════════════
import tempfile
import json, os, subprocess, sys, threading, time, hashlib, signal, heapq, tempfile
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# v1402 — Windows Hebrew/cp1255 consoles crash on emoji boot prints
# (UnicodeEncodeError) and die before the agent bridge opens. Force UTF-8
# stdio with replace so ON AIR never dies on a logo line.
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("PYTHONUTF8", "1")
    for _stream_name in ("stdout", "stderr"):
        _stream = getattr(sys, _stream_name, None)
        try:
            if _stream is not None and hasattr(_stream, "reconfigure"):
                _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

VERSION = "v1915"   # A thin TZ zone now says no with the cursor
HERE   = os.path.dirname(os.path.abspath(__file__))
FRAMES = os.environ.get("TV_FRAMES_DIR") or os.path.join(HERE, "frames")   # v752 — replay feeds its own watch dir
def _under(path, root):
    """Is `path` inside `root`? Case-normalised, because HIS WINDOWS MACHINE IS THE OTHER HALF.

    v1897 — this comparison was written four times tonight as `h.startswith(root + os.sep)`, and on
    Windows that is a coin flip: the same directory arrives as C:\\Users\\... from one call and
    c:\\users\\... from another, `startswith` says no, and the isolation rule silently decides a
    FIXTURE is his real tree — which is the exact class the whole night was spent closing, arriving
    on the machine I cannot run the suite on.

    os.path.normcase is a no-op on macOS and Linux and lowercases + normalises separators on
    Windows, so this is correct everywhere and changes nothing here. [[dual-machine-setup]]
    """
    try:
        a = os.path.realpath(path)
        b = os.path.realpath(root)
    except Exception:
        return False
    # THE FILESYSTEM IS THE AUTHORITY WHEN IT CAN ANSWER. os.path.samefile compares inodes, so it
    # is right on a case-INSENSITIVE volume (his Mac's APFS by default) where two spellings are one
    # directory — normcase alone says "different" there and would call his own tree a fixture.
    # Measured: TV_HIST set to the uppercased form of tv/frames/hist was treated as isolated, and
    # "isolated" writes would have landed in his real directory under a different spelling.
    try:
        if os.path.exists(a) and os.path.exists(b) and os.path.samefile(a, b):
            return True
    except Exception:
        pass
    # walk up: is any ancestor of `a` the same file as `b`? Handles the nested case with the same
    # authority, and stops at the root rather than looping.
    try:
        cur = a
        while True:
            parent = os.path.dirname(cur)
            if parent == cur:
                break
            cur = parent
            if os.path.exists(cur) and os.path.exists(b) and os.path.samefile(cur, b):
                return True
    except Exception:
        pass
    # neither exists yet (a fixture dir about to be created): fall back to normcase, which is a
    # no-op on posix and lowercases + normalises separators on Windows.
    a, b = os.path.normcase(a), os.path.normcase(b)
    return a == b or a.startswith(b + os.sep)


def _fixture_root(here):
    """The directory live state belongs in: his tree normally, the FIXTURE's when TV_HIST is one.

    v1869 — one rule, four files. A caller that repoints TV_HIST outside this module has said "this
    is not his world"; his console log, his engine state, his G5 stats and his subscription meter
    must not then describe a fixture's run. Measured tonight: a single gate run rewrote all four,
    and the pollution of ONE of them — control_agent.log — cost a wrong diagnosis, because the
    sim/live start banners I read as HIS button presses were written by my own test-spawned control
    apps. [[feedback-fixtures-never-touch-live-data]] [[feedback-suspect-the-instrument]]
    """
    hist = os.environ.get("TV_HIST")
    if hist:
        try:
            if not _under(hist, here):
                return os.path.realpath(hist)
        except Exception:
            pass
    return here


STATE  = os.path.join(_fixture_root(HERE), "state.json")
PORT   = int(os.environ.get("TV_PORT", "17771"))   # v711 — overridable (tests · port conflicts)
# v780 — one ON cycle = one theatre session. Every journal row carries this id so SIM/theatre
# never glues multiple restarts into one mega-run (the 10min gap alone was too soft).
SESSION_ID = ""
# v901 — PRODUCT: Auto Intake (default) vs Robot (FROZEN unless TV_ROBOT=1).
# Intake = settle on stash/loot → deep read → board feeds locked Tools/Vault 📸 pipelines.
ROBOT_MODE = str(os.environ.get("TV_ROBOT", "0") or "0").strip().lower() in ("1", "true", "yes", "on")
# v925 LIGHT (Konyo, acceptance day: 'so laggy i cant play a game even… like a reader, not
# needing to process so heavy… like screenshot not record… 1 claude is enough'). LIGHT is the
# DEFAULT product now: a gentle screenshot reader, not a screen recorder. No continuous film,
# a slow sensor tick, no OCR lane. Heavy capture (film/OCR/fast poll) is opt-in for the SIM
# debugger via TV_LIGHT=0. Robot mode implies heavy.
LIGHT_MODE = (not ROBOT_MODE) and str(os.environ.get("TV_LIGHT", "1") or "1").strip().lower() not in ("0", "false", "no", "off")
MIN_GAP_S    = float(os.environ.get("TV_MIN_GAP", "3.5" if not ROBOT_MODE else "1.5") or 3.5)
HEARTBEAT_S = max(1.0, min(20.0, float(os.environ.get("TV_HEARTBEAT", "8.0" if not ROBOT_MODE else "3.0") or 8.0)))
PRIORITY_GAP_S = float(os.environ.get("TV_PRIORITY_GAP", "1.0" if not ROBOT_MODE else "0.7") or 1.0)
SESSION_CAP  = 240
# v925 — the sensor tick: LIGHT samples the screen ~every 1.8s (loot waits on the ground), not
# ~7×/second. This poll capture (Grok: cut #2) is the biggest steady lag after the film loop.
POLL_S       = float(os.environ.get("TV_POLL", ("1.8" if LIGHT_MODE else "0.15") if not ROBOT_MODE else "0.12") or 0.15)
# v926.2 ADAPTIVE CADENCE (Konyo: 'once im in the game the screenshotter loops again and slows
# it') — a full-screen grab forces the Mac to read back the framebuffer, and doing that while a
# GPU game renders causes a brief hitch. So during ACTIVE play (screen changing = you're moving/
# fighting, nothing readable anyway) the reader backs off to PLAY_GAP_S; the instant you PAUSE
# (screen settles = loot/stash) it drops back to POLL_S and reads. Capture load is near-zero when
# you're playing hard, and only picks up when you stop to look — the one time a read matters.
PLAY_GAP_S   = float(os.environ.get("TV_PLAY_GAP", "4.0" if LIGHT_MODE else "1.0") or 4.0)
WATCH_MODE   = "--watch" in sys.argv

# ── v1595 — THE MINI FLAG. control_app has appended --mini=<secs> --mini-focus=<what> to this
# agent's argv since the mini endpoint landed, and this file parsed argv with bare `in sys.argv`
# checks, so BOTH were read as unknown words and dropped. The consequence was quiet and total: a
# mini run behaved exactly like ON AIR, and — the part that mattered — NO REEL WAS EVER STAMPED as
# mini, so vault_retro.is_mini_reel() could never once return True and its mini-first ordering was
# unreachable code sitting behind a condition nothing could satisfy.
#
# A parked stash session is the densest evidence in the whole archive: he is not fighting, the
# panel is held still, and every frame is a clean look at what he owns. That is exactly the footage
# the accumulator wants first, and it was indistinguishable from a boss run.
def _argv_val(flag, default=None):
    """--flag=value or --flag value. Returns default when absent or malformed."""
    pre = flag + "="
    for i, a in enumerate(sys.argv):
        if a.startswith(pre):
            return a[len(pre):]
        if a == flag and i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith("--"):
            return sys.argv[i + 1]
    return default

_mini_raw   = _argv_val("--mini")
MINI_MODE   = _mini_raw is not None
try:
    MINI_SECONDS = max(10, min(40, int(float(_mini_raw)))) if MINI_MODE else 0
except Exception:
    MINI_SECONDS = 25 if MINI_MODE else 0        # a garbled number is still a mini run
MINI_FOCUS  = (_argv_val("--mini-focus") or "stash") if MINI_MODE else ""
# v1783 — the FLAG BEING PRESENT is the choice. "stash" also arrives as the fallback above and as
# the console's pre-selected button, so the value alone cannot say whether he picked it.
MINI_FOCUS_CHOSEN = bool(_argv_val("--mini-focus")) if MINI_MODE else False
if MINI_MODE:
    print(f"⏱ MINI CAPTURE — {MINI_SECONDS}s, focus={MINI_FOCUS}", flush=True)
MOTION_PEAK  = 0.10
SETTLE       = 0.03
_FILM_FPS = max(4, min(30, int(float(os.environ.get("TV_FILM_FPS", "5" if not ROBOT_MODE else "8") or 5))))
FILM_INTERVAL_S = 1.0 / float(_FILM_FPS)
_FOOTAGE_FPS = max(1, min(5, int(float(os.environ.get("TV_FOOTAGE_FPS", "1") or 1))))
FOOTAGE_INTERVAL_S = 1.0 / float(_FOOTAGE_FPS)
FILM_MAX_PX = max(1280, min(3840, int(os.environ.get("TV_FILM_MAX_PX", "1440" if not ROBOT_MODE else "1600") or 1440)))
FILM_JPEG_Q = max(55, min(95, int(os.environ.get("TV_FILM_Q", "72" if not ROBOT_MODE else "75") or 72)))
_FILM_TIMES = deque(maxlen=64)

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
PROMPT_VER = "p1839"   # v1839 — the readers now separate "not a Chronicle page" from "cannot judge these rows"; bump whenever READ_PROMPT changes
_LAST_RAW = ""        # v832 (SIMULATION_SPEC) — the model's literal words for the read in flight
READ_PROMPT = (
    "Image {path} = Diablo II Resurrected (RoW). Reply with STRICT JSON only, no markdown, no prose:\n"
    "{{\"area\":\"\",\"tz\":[],\"scene\":\"gameplay\",\"stashTab\":\"\",\"chronicleTab\":\"\",\"names\":[],\"names_loc\":{{}},\"sockets\":{{}},\"discovered\":[],\"conf\":0.0}}\n"
    "scene = one of: town | stash | inventory | loot | gameplay | transition | chronicle.\n"
    # v1509 — THE CHRONICLE SCENE. Konyo: "when chronicle/menu is clicked ingame it should
    # automatically know we are about to register and read and analyze the CHRONICLE lists."
    # This is the scene the whole auto-tally arc hangs off: nothing downstream can fire while the
    # classifier has no word for the screen. The UNIQUES/SETS split is not cosmetic — they are two
    # different ledgers (d2r_foundLog vs d2r_setPieces, 243/403 and 108/135), and a Sets screen
    # tallied as Uniques is worse than no tally at all, so the tell is spelled out rather than left
    # to the model's judgement.
    "chronicle = the in-game HOLY GRAIL / CHRONICLE panel: a scrollable LIST of item names with "
    "found/unfound styling, opened from the menu. It is NOT the stash and NOT the inventory — there "
    "is no grid of item icons to pick up, only rows of names. "
    # v1773 — MEASURED, NOT IMAGINED. Called directly on his 08-17 frames: a page where his cursor
    # rested on a row — so the game painted a large item stat tooltip over the list — came back
    # scene='transition' at conf 0.85 with zero names, while two clean pages from the same reel came
    # back chronicle/uniques with 6 names each. The tell for `transition` two paragraphs down is the
    # ABSENT bottom HUD, and that frame showed the life orb, the mana orb and the belt row plainly;
    # the popup simply dominated the picture. classify() runs once per RUN, so that one answer
    # discarded up to 44 Chronicle pages behind it. v1773 gives a refused run a second opinion, but
    # a workaround downstream is not a reason to leave the reader wrong here.
    "A large ITEM TOOLTIP (a floating stat block: damage, requirements, blue affix lines) often "
    "covers part of this panel when the cursor rests on a row. That is still scene=chronicle — the "
    "CHRONICLE title bar, the Unique/Sets/Runewords tabs and the rows around the popup are the tell. "
    "It is NEVER a transition: a transition has no bottom HUD, and this panel is drawn over a live "
    "game with the life and mana orbs still on screen. Read whatever rows the popup leaves visible.\n"
    "chronicleTab = ONLY when scene=chronicle: which ledger is on screen. "
    "\"uniques\" = the unique-item list (single items: Shako, Windforce, Stormshield). "
    "\"sets\"    = the set list (rows grouped under set NAMES: Tal Rasha, Immortal King, Tancred). "
    "If you cannot tell which of the two it is, leave chronicleTab \"\" — an unknown ledger is "
    "recoverable, a wrong one silently corrupts the other ledger.\n"
    "When scene=chronicle put EVERY item name you can read in names[], in the order shown, and put "
    "the found/claimed ones in discovered[]. A partial or scrolled list is expected and fine — "
    "never invent names to fill a page.\n"
    "chronicleSort = ONLY when scene=chronicle: the sort control at the TOP RIGHT of the panel, read "
    "literally. \"newest\" if it says Newest to Oldest, \"oldest\" if Oldest to Newest, \"other\" for any "
    "other ordering, \"\" if it is not visible. This is what decides whether the TOP of the list is his "
    "most recent finds, so guessing it is worse than leaving it blank.\n"
    "foundAt = ONLY when scene=chronicle: map each item name -> its exact 'First Found:' stamp, copied "
    "digit for digit, e.g. {{\"Razorswitch\":\"08/20/2026, 00:49\"}}. NEVER infer a date from a row's "
    "position in the list, and omit any row whose stamp is covered by a tooltip or cut off at the panel "
    "edge — a missing stamp is recoverable, an invented one is a false find date forever.\n"
    "droppedBy = ONLY when scene=chronicle: map each item name -> the monster on its 'Dropped By:' line, "
    "e.g. {{\"Razorswitch\":\"Infector of Souls\"}}. Omit what you cannot read.\n"
    "⚠ THE TWO TABS PRINT THOSE LINES IN OPPOSITE ORDER — measured on his frames, not assumed. On "
    "UNIQUE a row reads: name / 'First Found: ...' / 'Dropped By: ...'. On SETS it reads: name / "
    "'Dropped By: ...' / 'First Found: ...'. Read each line by its LABEL, never by its position under "
    "the name, or every set piece gets a monster where its date belongs.\n"
    "transition = fullscreen loading/portal art: the burning fire portal, act loading screen, or a "
    "dark frame with NO bottom HUD. THE DECIDING TELL: if the bottom HUD (belt row / red life + blue "
    "mana orbs / skill bar) is ABSENT the frame is transition; a dark COMBAT frame (night, a cave, a "
    "dim boss room) STILL shows that HUD, so it stays gameplay. The player is entering a portal, "
    "waypoint, or a new game — names are expected empty; if an 'ENTERING <zone>' banner is legible put "
    "that zone in area, else leave area \"\".\n"
    "area = zone name from top-right Game block / ENTERING banner / automap, else \"\".\n"
    "tz = purple terror-zone lines in that block, else [].\n"
    "stashTab = ONLY when scene=stash: which LEFT stash tab is active — "
    "personal | shared | gems | materials | runes | \"\" if unknown. "
    "Stash tell: left panel tabs + inventory often open on the right.\n"
    "names = READABLE text labels only (tooltips first line, ground loot labels, open inventory/stash "
    "name text). Never invent from icons alone. Never complete partial names.\n"
    "sockets = for any item whose tooltip shows a 'Socketed (N)' line OR N visible empty socket "
    "holes, map its exact name -> N (integer), e.g. {{\"Diadem\":3}}. Omit items with no sockets; "
    "{{}} if none. Read the number from the tooltip, never guess from the base type.\n"
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
    "inventory/stash: list anchors (Horadric Cube, Tome of Town Portal, Tome of Identify) when visible "
    "BUT prioritize NEW tooltips / names that are not the always-on cube+tomes.\n"
    "conf = 0.0-1.0 confidence. Be fast and precise."
)

# v926 SECOND LOOK (Konyo: 'it can check and verify and recheck and reverify and literally be
# more accurate') — LIGHT freed the machine, so the reader spends the idle gap DOUBLE-CHECKING
# each item read against the SAME archived screenshot. A closed-set confirm first, then a tight
# open pass for anything clearly missed. Corrections flow through the SAME lifecycle/funnel pipes.
VERIFY_ON = str(os.environ.get("TV_VERIFY", "1" if LIGHT_MODE else "0")).strip().lower() in ("1", "true", "yes", "on")
VERIFY_PROMPT = (
    "Image {path} = the SAME Diablo II Resurrected screenshot a first reader already looked at.\n"
    "It reported these item names: {prior}.\n"
    "Look at the screenshot AGAIN, carefully, and correct that reading. STRICT JSON only:\n"
    "{{\"confirm\":[],\"missed\":[],\"not_present\":[],\"conf\":0.0}}\n"
    "confirm = names from the reported list that ARE clearly present on screen.\n"
    "not_present = names from the reported list that are NOT actually on screen (misreads/hallucinations).\n"
    "missed = item names CLEARLY readable on screen but absent from the reported list (max 5). "
    "Only add a name you can actually read as text — never from an icon, never a guess.\n"
    "conf = 0.0-1.0 confidence in this correction. Be strict: when unsure, prefer confirm over change."
)

# v752 — persistent session journal (tv/sessions.jsonl, gitignored): every published read
# appended as one JSON line. This is what `tvd replay` re-runs — real frames, real reads.
def _journal_path():
    """Where session rows are appended — and NEVER his live journal when the frames are a fixture.

    v1866 — MEASURED, NOT SUSPECTED: 1,729 rows in tv/sessions.jsonl carry a `_dur` session id and
    the note "durability-harness". That is test_reel_index_durability.py, which correctly gives its
    child an isolated TV_HIST and TV_FRAMES_DIR — and never knew there was a THIRD path to isolate.
    75% of the session_end rows in his journal are from a test harness, still arriving during gate
    runs tonight.

    The fix is the one his scar names: GUARD THE FIXTURE, NOT THE CALL SITE. A caller that isolates
    the frames has said, unmistakably, "this is not his world"; a journal beside those frames is the
    only journal that can describe them. So an overridden hist that does not live under this module
    implies an overridden journal, and a test that forgets is protected anyway.

    TV_SESSIONS still wins when set explicitly — the CI harness has always used it and knows what it
    is asking for. [[feedback-fixtures-never-touch-live-data]]
    """
    explicit = os.environ.get("TV_SESSIONS")
    if explicit:
        return explicit
    hist = os.environ.get("TV_HIST")
    if hist:
        try:
            h = os.path.realpath(hist)
            if not _under(hist, HERE):
                return os.path.join(h, "sessions.jsonl")
        except Exception:
            pass
    return os.path.join(HERE, "sessions.jsonl")


JOURNAL = _journal_path()   # v877 — CI harness override; v1866 — an isolated hist isolates this too
_JOURNAL_WARNED = False
_JQ = None   # v879 (Grok A-(a)) — ONE writer thread preserves apply order; emit never blocks on fsync
def _journal_writer_loop():
    while True:
        rec = _JQ.get()
        if rec is None:
            _JQ.task_done()
            return
        try:
            _journal_write(rec)
        except Exception as e:
            # v886 — a lost journal row is a lost read FOREVER: say so, loudly
            try:
                print(f"  ⚠ JOURNAL WRITE FAILED ({type(e).__name__}: {str(e)[:120]}) — read row lost", flush=True)
                ev("cap", f"journal write failed: {type(e).__name__}")
            except Exception:
                pass
        _JQ.task_done()


def _journal_flush(timeout=10.0):
    """v880 (Grok back-pass #3) — a REAL join: queue.empty() goes true before the fsync
    finishes; task_done() fires only after the write. join() in a helper thread + timeout."""
    try:
        if _JQ is None:
            return
        done = threading.Event()
        def _j():
            try:
                _JQ.join()
            except Exception:
                pass
            done.set()
        threading.Thread(target=_j, daemon=True).start()
        done.wait(timeout)
    except Exception:
        pass


def _journal(rec):
    """v879 — enqueue when the writer runs; direct write otherwise (tests/replay).

    v1866 — EVERY ROW A SIMULATION WRITES SAYS SO. Konyo's own journal holds 414 rows produced
    under TV_STUB across ten days, sitting beside real ones with nothing on them to tell the
    difference except `mode: "stub"` on the deep-read rows — and a session's summary rows carry no
    mode at all, so a whole SIM session was indistinguishable from a live one that saw nothing.

    That mattered tonight: while MINI was dead (v1863) he pressed buttons, and control_agent.log
    records five starts in 64 seconds alternating sim · live · live · sim. He then reported "i did
    a regular LIVE SESSION it worked" and asked why the readers had not read his Sets chronicle.
    Under TV_STUB the deep reader returns canned rows whose scene defaults to "gameplay", so a
    Chronicle page open on screen is journaled as gameplay and nothing is wrong with the reader.

    THE EXPOSURE IS REAL AND HAS NOT FIRED — say both halves. stub_manifest.json carries real item
    names ("Ars Dul'Mephistos", "Skin of the Vipermagi", "Ist Rune"), and nothing excluded a sim
    reel from a sweep. It never landed because the manifest is keyed by basenames his reels never
    use (pit_loot.jpg, town_stash.jpg) and the "*" fallback returns names: []. Measured: 0 of 414
    stub rows carry a canned name. A guard that depends on a filename not colliding is not a guard,
    so the flag is the guard. [[feedback-fixtures-never-touch-live-data]]
    """
    try:
        if os.environ.get("TV_STUB") and isinstance(rec, dict) and "sim" not in rec:
            rec = dict(rec)
            rec["sim"] = True
    except Exception:
        pass
    if _JQ is not None:
        try:
            _JQ.put(dict(rec) if isinstance(rec, dict) else rec)
            return
        except Exception:
            pass
    _journal_write(rec)


def _journal_write(rec):
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
_STATE_MEM = None          # v879 (Grok A) — the AUTHORITATIVE state lives in memory
_STATE_PATH = None         # path key: tests/replay repoint STATE — the cache follows
_STATE_DIRTY = [False]
def _load():
    """v879 — one cold disk read per process; every later _load() is the in-memory dict.
    The old per-call json.load ran at 4Hz from /state AND inside every apply."""
    global _STATE_MEM, _STATE_PATH
    if _STATE_MEM is None or _STATE_PATH != STATE:
        _STATE_PATH = STATE
        _STATE_MEM = None
    if _STATE_MEM is None:
        try:
            with open(STATE, encoding="utf-8") as f:
                _STATE_MEM = json.load(f)
        except Exception:
            _STATE_MEM = {"online": True, "startedAt": int(time.time()*1000), "reads": [], "readCount": 0}
    return _STATE_MEM

def _save(st):
    """v879 — WRITE-BEHIND: callers mark dirty; the saver thread (or a flush) hits disk.
    st is the in-memory dict (or replaces it — replay/tests pass fresh dicts)."""
    global _STATE_MEM, _STATE_PATH
    _STATE_MEM = st
    _STATE_PATH = STATE
    _STATE_DIRTY[0] = True

def _state_flush():
    """Serialize the in-memory state to disk (atomic replace). Called by the saver thread,
    at seal, and at farewell — Grok flush list items 3/6."""
    st = _STATE_MEM
    if st is None:
        return
    tmp = STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f: json.dump(st, f)
    os.replace(tmp, STATE)
    _STATE_DIRTY[0] = False

def _state_saver_loop():
    while True:
        time.sleep(1.0)
        try:
            if _STATE_DIRTY[0]:
                with _state_lock:
                    _state_flush()
        except Exception:
            pass

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
         "throttled": _is_throttled(),   # v891 — the 🐢 chip's truth
         "footageFps": _foot_fps,   # v861 — the archive floor, alarmed by the UI
         "visionBusyMs": (max(0, int(now * 1000) - _pool_oldest) if (_pool_pin and _pool_oldest) else 0),
         "poolInFlight": _pool_pin, "poolN": POOL_N,
         "poolWarm": sum(1 for _w9 in _WORKERS if getattr(_w9, "warm_ok", False)),   # v870
         "sessionMs": 0, "lastReadAgeMs": -1, "named": 0, "vaulted": 0,
         # v846 — Tesla-drive dashboard truth
         "filmFps": _film_fps_now(), "filmTargetFps": _FILM_FPS,
         "footageFps": _foot_fps_now(), "footageTargetFps": _FOOTAGE_FPS,
         "filmLane": globals().get("_FILM_LANE", ""), "filmCapMs": globals().get("_FILM_CAP_MS"),   # v867
         "footageWhy": globals().get("_FOOTAGE_WHY", ""),   # v947 — grab|bridge-last-good|disk-full
         "footageBridges": int(globals().get("_FOOTAGE_BRIDGES") or 0),
         "filmWhiteRejects": int(globals().get("_FILM_WHITE_REJECTS") or 0),
         "filmMaxPx": FILM_MAX_PX, "pollMs": int(POLL_S * 1000),
         # v944 — brains 1+2: live settle ring depth + un-read text-eye sweep backlog
         "settleQueue": len(_SETTLE_QUEUE), "textEyeBacklog": len(_TEXT_EYE_BACKLOG),
         "gapCruiseS": MIN_GAP_S, "gapPriorityS": PRIORITY_GAP_S,
         "heartbeatS": HEARTBEAT_S,
         # v899 — no-game guard: UI shows a sticky notice; AI stays dark until D2R.exe appears
         "gameOk": bool(globals().get("_GAME_OK", True)),
         "gameMsg": str(globals().get("_GAME_MSG") or ""),
         "aiPaused": bool(globals().get("_AI_PAUSED", False)),
         # v901 — product mode (Robot frozen unless TV_ROBOT=1)
         "productMode": ("robot" if ROBOT_MODE else "intake"),
         "robotMode": bool(ROBOT_MODE)}
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
        def do_OPTIONS(self):
            # v927.5 — CORS PREFLIGHT: the board (:17772 / bull-4-u.com) POSTs /intake_result
            # cross-origin with a JSON content-type, which triggers a preflight. Without this
            # handler every preflight 501'd, the POST died in the board's .catch, and
            # "TALLIES · synced" sat at 0 on EVERY surface while tallies actually landed.
            self.send_response(204)
            self.send_header("access-control-allow-origin", "*")
            self.send_header("access-control-allow-methods", "GET, POST, OPTIONS")
            self.send_header("access-control-allow-headers", "content-type")
            self.send_header("access-control-max-age", "3600")
            self.end_headers()
        def do_POST(self):
            # v902 (Konyo: 'wire the library to the AI READER and automatic intake') —
            # the board posts each auto-intake RESULT here; it becomes a journaled beat
            # (lane 'intake') time-synced to the frame the shot came from, so the SIM reel
            # and the session library show WHAT INTAKE DID, cross-referenced to the photo.
            if self.path.startswith("/intake_result"):
                try:
                    ln = int(self.headers.get("Content-Length") or 0)
                    body = json.loads(self.rfile.read(ln).decode("utf-8", "replace") or "{}") if ln else {}
                    now_ms = int(time.time() * 1000)
                    _ts = int(body.get("ts") or now_ms)
                    _fid = str(body.get("frameId") or "")[:48]
                    # A0 fix (2026-07-21, arch panel Q5 blocker): captureTs must be the FRAME's
                    # capture ms, not `_ts` (the receipt-landing time) — retro joins on captureTs,
                    # never ts, so a receipt stamped with receipt time desyncs from the frame it
                    # describes on the scrub. Only fall back to `_ts` when no frameId was sent
                    # (can't do better); capSrc flags which happened so retro readers know honestly.
                    _cap_from_frame = _capture_ts_from_frame_id(_fid)
                    _cap_ts = _cap_from_frame if _cap_from_frame is not None else _ts
                    _cap_src = "frame" if _cap_from_frame is not None else "receipt-fallback"
                    rec = {
                        "ts": _ts, "captureTs": _cap_ts,
                        "completedTs": now_ms,
                        "n": 0, "scene": "intake", "lane": "intake", "mode": "intake",
                        "names": [], "area": "", "sessionId": SESSION_ID,
                        "intake": {
                            "tab": str(body.get("tab") or "")[:24],
                            "kind": str(body.get("kind") or "")[:16],
                            "counts": body.get("counts") if isinstance(body.get("counts"), dict) else {},
                            "total": int(body.get("total") or 0),
                            "errors": int(body.get("errors") or 0),
                            "items": (body.get("items") or [])[:60],
                            "ok": bool(body.get("ok", True)),
                        },
                        "frameId": _fid,
                        "capSrc": _cap_src,
                        "note": ("📸 intake · " + str(body.get("tab") or body.get("kind") or "shot"))[:80],
                    }
                    _journal(rec)
                    with _state_lock:
                        st = _load()
                        st.setdefault("intakes", [])
                        st["intakes"].append({k: rec[k] for k in ("ts", "intake", "frameId", "note")})
                        st["intakes"] = st["intakes"][-60:]
                        _save(st)
                    self._hdr(); self.wfile.write(b'{"ok":true}')
                except Exception as e:
                    try:
                        self._hdr(); self.wfile.write(json.dumps({"ok": False, "msg": str(e)[:120]}).encode())
                    except Exception:
                        pass
                return
            self._hdr(); self.wfile.write(b'{"ok":false,"msg":"unknown"}')

        def do_GET(self):
            from urllib.parse import urlparse, parse_qs
            if self.path.startswith("/state"):
                # v770 (Grok R4 perf) — ?since=<ts> returns a THIN delta: full reads ring only
                # when asked from cold; 4 polls/sec no longer parse 200 rich reads every tick.
                # v1435/v1440 — ?lite=1 for control prober: readCount + eye + pin + beat, no fat rings.
                _q = parse_qs(urlparse(self.path).query or "")
                _since = 0
                try: _since = int((_q.get("since") or ["0"])[0])
                except Exception: _since = 0
                _lite = (_q.get("lite") or ["0"])[0] in ("1", "true", "yes")
                # v1419 — every state poll re-reads Windows pin so UI never sticks on eye arming
                if WATCH_MODE:
                    try:
                        _refresh_cap_target_from_disk()
                    except Exception:
                        pass
                with _state_lock:
                    st = _load(); st["online"] = True; st["now"] = int(time.time()*1000)
                    st["beat"] = dict(_BEAT); st["events"] = list(_EVENTS); st["ap"] = dict(_AP)
                    st["stopping"] = _STOPPING   # v777.2 — 1-1 sync: the board drops the INSTANT the farewell begins
                    st["captureTarget"] = dict(_CAP_TARGET)  # v772 — window pin (CrossOver/D2R) or full
                    st["eyeAgeMs"] = _eye_age_ms()   # v785 — film honesty: stage drops LIVE when this goes stale
                    st["health"] = _health(st)   # v789 — fault-lamp truth (Grok R4 #1)
                    st["sessionId"] = SESSION_ID
                    # v880 (Grok back-pass P0) — _STATE_MEM is AUTHORITATIVE now: the ?since=
                    # thin-delta must filter a COPY (the old code truncated the live ring and
                    # popped seen/farmed from the real state), and serialization happens under
                    # the lock so a concurrent apply can't resize dicts mid-dump.
                    if _lite:
                        # v1440 — tiny payload for control_app prober (~smooth under D2R)
                        _rc = st.get("readCount")
                        if _rc is None:
                            _rc = len(st.get("reads") or [])
                        out = {
                            "online": True,
                            "now": st["now"],
                            "ver": VERSION,
                            "readCount": int(_rc or 0),
                            "eyeAgeMs": st["eyeAgeMs"],
                            "captureTarget": st["captureTarget"],
                            "beat": st["beat"],
                            "sessionId": st.get("sessionId") or "",
                            "gameOk": st.get("gameOk", True),
                            "aiPaused": st.get("aiPaused", False),
                            "gameMsg": st.get("gameMsg") or "",
                            "health": {
                                "eyeAgeMs": (st.get("health") or {}).get("eyeAgeMs", st["eyeAgeMs"]),
                                "footageFps": (st.get("health") or {}).get("footageFps"),
                                "visionBusyMs": (st.get("health") or {}).get("visionBusyMs"),
                                "sessionMs": (st.get("health") or {}).get("sessionMs"),
                                "lastReadAgeMs": (st.get("health") or {}).get("lastReadAgeMs"),
                                "aiPaused": (st.get("health") or {}).get("aiPaused"),
                                "gameOk": (st.get("health") or {}).get("gameOk", True),
                                "gameMsg": (st.get("health") or {}).get("gameMsg") or "",
                            },
                            "events": list(_EVENTS)[-4:],
                            "stopping": st["stopping"],
                            "lite": True,
                        }
                    else:
                        out = dict(st)
                        if _since:
                            out["reads"] = [r for r in (st.get("reads") or []) if (r.get("ts") or 0) > _since]
                            out.pop("seen", None); out.pop("farmed", None)
                    payload = json.dumps(out).encode()
                try:
                    self._hdr(); self.wfile.write(payload)
                except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError):
                    # v1430 — control aborts slow /state under D2R; never traceback-spam the log
                    pass
            elif self.path.startswith("/ping"):
                try:
                    self._hdr(); self.wfile.write(b'{"ok":true,"tv":"diablo"}')
                except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError):
                    # v1430 — Windows clients abort mid-write under load (WinError 10053 spam)
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
                        # v1440 — no-store keeps film live; max-age=0 is belt for WebView2
                        self.send_header("cache-control", "no-store, max-age=0")
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
# v935.7 — boot safe: never "full" until a real pin exists (text-eye / film obey this)
_CAP_TARGET = {"mode": "waiting", "label": "eye arming…", "wid": None}


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


def _screencapture_window(wid, tmp_path, fmt="bmp", timeout=2.0):
    """Try macOS screencapture -l. Short default timeout — CrossOver D2R.exe often hangs -l forever."""
    try:
        r = subprocess.run(
            ["screencapture", "-l", str(int(wid)), "-o", "-x", "-t", fmt, tmp_path],
            capture_output=True, timeout=timeout, **NICE_KW)
        return os.path.isfile(tmp_path) and os.path.getsize(tmp_path) > 10000
    except Exception:
        return False


def _capture_window_to_bmp(wid, path, timeout=12):
    """v898 — pin a window to BMP for the intelligence loop.
    Quartz FIRST (D2R.exe under CrossOver: ~0.2–0.8s). screencapture -l is last-resort
    with a short timeout — it hangs 5–12s on this surface and starved live.bmp / NO EYE."""
    tmp = _cap_tmp(path)
    try:
        # 1) Quartz JPEG (fast) → sips BMP
        qj = path + ".qz.jpg"
        if _quartz_grab_window(wid, qj, uti="public.jpeg"):
            try:
                subprocess.run(
                    ["sips", "-s", "format", "bmp", qj, "--out", tmp],
                    capture_output=True, timeout=min(8, max(3, timeout)), **NICE_KW)
            except Exception:
                pass
            try:
                if os.path.exists(qj):
                    os.remove(qj)
            except Exception:
                pass
            if _cap_promote(tmp, path, min_bytes=8000):
                return True
        # 2) Quartz PNG → sips BMP (heavier, still better than hung screencapture)
        png = path + ".qz.png"
        if _quartz_grab_window(wid, png, uti="public.png"):
            try:
                subprocess.run(
                    ["sips", "-s", "format", "bmp", png, "--out", tmp],
                    capture_output=True, timeout=min(8, max(3, timeout)), **NICE_KW)
            except Exception:
                pass
            try:
                if os.path.exists(png):
                    os.remove(png)
            except Exception:
                pass
            if _cap_promote(tmp, path, min_bytes=8000):
                return True
        # 3) screencapture -l last, hard-capped (never block the poll loop)
        sc_t = min(2.0, float(timeout) if timeout else 2.0)
        if _screencapture_window(wid, tmp, fmt="bmp", timeout=sc_t):
            if _cap_promote(tmp, path):
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

def _sips_pixel_size(src):
    """Return (w, h) from sips, or (0, 0) on failure. Used to avoid upsample."""
    try:
        r = subprocess.run(
            ["sips", "-g", "pixelWidth", "-g", "pixelHeight", src],
            capture_output=True, text=True, timeout=5, **NICE_KW)
        w = h = 0
        for line in (r.stdout or "").splitlines():
            if "pixelWidth:" in line:
                try: w = int(line.split(":")[-1].strip())
                except Exception: pass
            elif "pixelHeight:" in line:
                try: h = int(line.split(":")[-1].strip())
                except Exception: pass
        return w, h
    except Exception:
        return 0, 0


def _sips_hd_jpeg(src, dest, max_px=None, quality=None, timeout=6):
    """HD+ JPEG for film stage. Default 2560px / q82 (4K-class polish, still WebView-friendly).

    v1450 — only pass --resampleHeightWidthMax when the source is LARGER than max_px.
    On current macOS, sips *upsamples* small images to that max (48×48 → 2560×2560),
    which bloated hist frames and broke the 'JPEG smaller than BMP' archive invariant."""
    max_px = FILM_MAX_PX if max_px is None else max_px
    quality = FILM_JPEG_Q if quality is None else quality
    try:
        cmd = ["sips", "-s", "format", "jpeg", "-s", "formatOptions", str(quality)]
        w, h = _sips_pixel_size(src)
        if max_px and w and h and max(w, h) > int(max_px):
            cmd += ["--resampleHeightWidthMax", str(int(max_px))]
        cmd += [src, "--out", dest]
        r = subprocess.run(cmd, capture_output=True, timeout=timeout, **NICE_KW)
        return r.returncode == 0 and os.path.isfile(dest) and os.path.getsize(dest) > 4000
    except Exception:
        return False


def _is_white_backing(path, size_ceiling=300_000):
    """v944 (Konyo live 'FOOTAGE STARVE — 0.2fps'): the Metal fullscreen surface hands
    Quartz a BLANK WHITE backing that still 'succeeds' (v930.3). The old guard rejected
    EVERY window grab under 150KB — but a legit DARK stash / loading frame ALSO compresses
    small, so his stash-heavy session starved: real dark frames were rejected -> demote ->
    the slow screencapture fallback cascade (2s+5s timeouts) -> ~0.45fps of full-screen frames.

    Smarter blank test: a grab is the artifact ONLY when it is near-uniform AND bright.
      · Legit game frame  -> UI/text/icons -> WIDE pixel spread          -> KEEP
      · Legit dark stash  -> orbs/belt/items on a dark field -> spread    -> KEEP
      · Legit black screen (loading/transition) -> near-uniform but DARK  -> KEEP
      · Metal white backing (mean~255, spread~0)                          -> REJECT
    Proven: 0 false-positives across 1736 real archived frames; the known ~93577-byte white
    class (mean~255, spread~0) still fails. Keeps the real-pixels law (REG-033) intact."""
    try:
        if os.path.getsize(path) > size_ceiling:
            return False   # real game frames run ~300KB-1.9MB; never the ~93KB white artifact
    except Exception:
        return True        # unreadable grab == unusable, treat as failure
    try:
        from PIL import Image, ImageStat
        with Image.open(path) as im:
            im.draft("L", (64, 64))       # fast partial decode (~11ms even on a 1.9MB retina jpg)
            g = im.convert("L")
            g.thumbnail((48, 48))
            lo, hi = g.getextrema()
            if (hi - lo) >= 24:           # wide spread -> real pixels, keep
                return False
            return ImageStat.Stat(g).mean[0] > 230   # near-uniform AND bright = white Metal backing
    except Exception:
        # PIL unavailable/corrupt: fall back to the pre-v944 size law so the white class is
        # still rejected (no worse than before) rather than the loop trusting a blank frame.
        try:
            return os.path.getsize(path) < 150_000
        except Exception:
            return True


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


def _archive_footage_copy(src_path, now_f, why="ok", _consume_due=True):
    """v947 — 1fps archive helper. Always advances the due clock; never blocks on sips.

    v1190 — promote-via-tmp: this was the one archive writer in the file that skipped the
    _cap_promote law every window/screen grab already follows ('write tmp, only promote when
    THIS call wrote real bytes' — see _cap_promote's own docstring on 'the stale-file lie').
    A copyfile() interrupted partway (ENOSPC, a kill, disk yanked) used to leave a truncated
    fragment sitting under the FINAL f_<ms>.jpg name — worse than a dropped frame, since nothing
    downstream re-checks size before treating a file at that name as a real archived frame; it
    silently pollutes the film reel forever. Now: copy to a private tmp, verify real bytes,
    os.replace (atomic on the same volume) into the final name — same law, same pattern as
    _cap_promote. Applied to the eye.last.jpg starve-bridge source too, since a corrupt bridge
    source would re-propagate into every later 'bridge-last-good' frame until film recovers.

    v1195 — _consume_due=False: the film loop's never-starve path can call this TWICE for the
    SAME now_f in one tick — a fresh grab first, then a bridge-last-good fallback if that fresh
    write fails (disk pressure, a torn copy). Both calls used to run the full due-gate: the
    first one (whether it went on to succeed or fail) already advanced _FOOTAGE_DUE past now_f,
    so the second call's OWN due-gate check (`now_f < _due`) then always rejected it before it
    could even try — the exact fallback this file's anti-starve law exists for was silently
    dead code whenever the primary write failed for a reason unrelated to frame content. The
    caller now owns the due-gate/advance for that one shared now_f slot and passes
    _consume_due=False to both attempts, so whichever one actually has bytes to write gets to."""
    try:
        if _consume_due:
            _iv = FOOTAGE_INTERVAL_S
            _due = globals().get("_FOOTAGE_DUE", 0.0)
            if now_f < _due:
                return False
            globals()["_FOOTAGE_DUE"] = max(_due + _iv, now_f - (_iv - 0.01)) if _due else now_f + _iv
        globals()["_FOOTAGE_AT"] = now_f
        globals()["_FOOTAGE_WHY"] = why
        if not src_path or not os.path.isfile(src_path) or os.path.getsize(src_path) < 4000:
            globals()["_FOOTAGE_REJECTS"] = int(globals().get("_FOOTAGE_REJECTS") or 0) + 1
            return False
        # ── v1548 — THE WARM-UP GATE ────────────────────────────────────────────────────────────
        # 16 of the 17 blank captures in his worst reel land in the FIRST NINETEEN SECONDS: capture
        # starts while D2R is still launching, so the window exists — the grab succeeds, the file is
        # a perfectly valid 2940x1912 JPEG well past the 4000-byte floor — and it is blank.
        #
        # v1543 stopped paying to classify them and v1545 marked them at seal. This stops making
        # them, which is the only one of the three that costs nothing at all.
        #
        # It gates ONLY the warm-up. Once one painted frame has landed the gate opens for the rest of
        # the session, permanently — a blank frame LATER is not startup noise, it is the game
        # crashing or the window vanishing, and that is evidence worth keeping rather than a fault to
        # suppress. Suppressing it would hide the very thing a watchdog exists to notice.
        if not globals().get("_FOOTAGE_WARM"):
            try:
                import chronicle_retro as _cr
                if _cr.is_dead_frame(src_path):
                    globals()["_FOOTAGE_WARMSKIP"] = int(globals().get("_FOOTAGE_WARMSKIP") or 0) + 1
                    globals()["_FOOTAGE_WHY"] = "warming-up (window not painted yet)"
                    return False
                globals()["_FOOTAGE_WARM"] = True
            except Exception:
                # cannot measure -> cannot refuse. An unmeasurable frame is archived, because
                # dropping what we could not judge is how real footage goes missing.
                globals()["_FOOTAGE_WARM"] = True
        hist_dir = HIST_DIR
        os.makedirs(hist_dir, exist_ok=True)
        import shutil as _sh
        if _sh.disk_usage(hist_dir).free / 1e9 < MIN_FREE_GB:
            globals()["_FOOTAGE_WHY"] = "disk-full"
            return False
        dest = os.path.join(hist_dir, "f_%d.jpg" % int(now_f * 1000))
        tmp = _cap_tmp(dest)
        try:
            _sh.copyfile(src_path, tmp)
            if not (os.path.isfile(tmp) and os.path.getsize(tmp) >= 4000):
                raise IOError("short/failed footage copy — not promoting a fragment")
            os.replace(tmp, dest)   # dest only ever holds complete bytes, never a torn write
        finally:
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except Exception:
                pass
        _FOOT_TIMES.append(now_f)
        # remember last GOOD archive source for starve-bridge — same tmp+promote law
        last = os.path.join(FRAMES, "eye.last.jpg")
        last_tmp = _cap_tmp(last)
        try:
            _sh.copyfile(src_path, last_tmp)
            if os.path.isfile(last_tmp) and os.path.getsize(last_tmp) >= 4000:
                os.replace(last_tmp, last)
                globals()["_FILM_LAST_GOOD"] = last
            else:
                globals()["_FILM_LAST_GOOD"] = src_path
        except Exception:
            globals()["_FILM_LAST_GOOD"] = src_path
        finally:
            try:
                if os.path.exists(last_tmp):
                    os.remove(last_tmp)
            except Exception:
                pass
        return True
    except Exception:
        return False


def _grab_full_screen_frame(tmp):
    """v1181 — full-screen grab + the SAME white-Metal-backing guard the window lane already
    applies via _is_white_backing (v944). Without this, the full-screen lane could archive a
    blank frame as real film: it is invoked specifically WHEN the window lane just white-rejected
    (demoted for the next 5s), i.e. exactly the moment a Metal transition is most likely to hand
    the desktop compositor the same blank surface — the gap the window lane was built to close,
    left open one lane over. Returns True only when a real (non-blank) frame is sitting at tmp;
    on reject/failure the tmp file is cleaned up so callers can treat False uniformly."""
    wrote = _quartz_grab_screen(tmp, uti="public.jpeg")
    if not wrote:
        try:
            subprocess.run(
                ["screencapture", "-x", "-t", "jpg", tmp],
                capture_output=True, timeout=1.5, **NICE_KW)
            wrote = os.path.exists(tmp) and os.path.getsize(tmp) > 4000
        except Exception:
            wrote = False
    if wrote:
        try:
            if _is_white_backing(tmp):
                wrote = False
                globals()["_FILM_WHITE_REJECTS"] = int(globals().get("_FILM_WHITE_REJECTS") or 0) + 1
        except Exception:
            wrote = False
    if not wrote:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass
    return wrote


def _film_loop():
    """v846/v947 TESLA DRIVE film — high-FPS HD JPEG of the pinned D2R window.
    Target TV_FILM_FPS (~5). Intelligence still uses BMP+frame_sig on the poll loop.
    Claude thinking never freezes this thread.

    v947 FOOTAGE STARVE fix (Konyo live 0.4fps):
      · white-backing reject → immediate full-screen Quartz (no 3-fail wait)
      · demote window lane 5s (was 15s)
      · never-starve screencapture timeout 1.5s (was 5s) — a long hang IS the starve
      · when grab fails but archive is DUE, bridge with last-good eye (better than a gap)
    """
    eye = os.path.join(FRAMES, "eye.jpg")
    tmp = eye + ".part.jpg"
    _lane_fail = 0
    _lane_full_until = 0.0
    while True:
        # v1199 — monotonic, not wall-clock: t0 only ever measures THIS iteration's own elapsed
        # time (capture duration + the cadence sleep below), never a stamp anyone else reads.
        # time.time() can jump BACKWARD (NTP correction, sleep/wake resync — routine on a Mac
        # left running for hours) — when it does, `dt = time.time() - t0` goes deeply negative
        # and `time.sleep(max(0.02, FILM_INTERVAL_S - dt))` turns into a sleep of however long
        # the clock jumped, freezing the film thread (0 real frames) for the whole gap. monotonic
        # never jumps backward, so cadence pacing can't be hijacked by a wall-clock correction.
        t0 = time.monotonic()
        try:
            if globals().get("_AI_PAUSED") and not WATCH_MODE:
                time.sleep(1.5)
                continue
            if not WATCH_MODE and (_CAP_TARGET or {}).get("mode") == "waiting":
                time.sleep(1.5)
                continue
            os.makedirs(FRAMES, exist_ok=True)
            wid = (_CAP_TARGET or {}).get("wid")
            if (_CAP_TARGET or {}).get("mode") == "waiting":
                wid = None
            if time.time() < _lane_full_until:
                wid = None
            wrote = False
            white_reject = False
            if wid:
                wrote = _quartz_grab_window(wid, tmp, uti="public.jpeg")
                if wrote:
                    try:
                        if _is_white_backing(tmp):
                            wrote = False
                            white_reject = True
                            globals()["_FILM_WHITE_REJECTS"] = int(globals().get("_FILM_WHITE_REJECTS") or 0) + 1
                    except Exception:
                        wrote = False
                if wrote:
                    _lane_fail = 0
                else:
                    _lane_fail += 1
                    # v947 — white Metal backing: skip doomed -l retries, go full-screen now
                    if white_reject or _lane_fail >= 2:
                        try:
                            r = subprocess.run(
                                ["screencapture", "-l", str(wid), "-o", "-x", "-t", "jpg", tmp],
                                capture_output=True, timeout=1.5, **NICE_KW)
                            wrote = os.path.exists(tmp) and os.path.getsize(tmp) > 4000
                            if wrote:
                                try:
                                    if _is_white_backing(tmp):
                                        wrote = False
                                        white_reject = True
                                except Exception:
                                    wrote = False
                        except Exception:
                            wrote = False
                        if wrote:
                            _lane_fail = 0
                    if not wrote:
                        # demote 5s (was 15) — recover window pin fast when surface returns
                        _need = 1 if (white_reject or globals().get("_LANE_DEMOTED_ONCE")) else 2
                        if _lane_fail >= _need:
                            _lane_full_until = time.time() + 5.0
                            _lane_fail = 0
                            globals()["_LANE_DEMOTED_ONCE"] = True
                            globals()["_FILM_LANE"] = "full(demoted)"
            if not wrote:
                # full-screen lane (demoted OR no wid OR white reject recovery)
                # v1251 — never wallpaper the film: full-screen only when D2R.exe is alive
                # and Screen Recording is granted (same law as capture_mac).
                if _allow_fullscreen_game_fallback("film"):
                    wrote = _grab_full_screen_frame(tmp)
                else:
                    wrote = False
            globals()["_FILM_LANE"] = (
                "window" if (wid and wrote and not white_reject and time.time() >= _lane_full_until)
                else ("full(demoted)" if time.time() < _lane_full_until else "full")
            )
            globals()["_FILM_CAP_MS"] = int((time.monotonic() - t0) * 1000)
            if wrote and os.path.exists(tmp) and os.path.getsize(tmp) > 4000:
                now_f = time.time()
                _archive_footage_copy(tmp, now_f, why="grab")
                # reap old film if disk tight
                try:
                    if now_f >= globals().get("_REAP_DUE", 0.0):
                        globals()["_REAP_DUE"] = now_f + 120.0
                        hist_dir = HIST_DIR
                        import shutil as _shu2
                        if _shu2.disk_usage(hist_dir).free / 1e9 < MIN_FREE_GB:
                            _yc = (time.time() - 900.0) * 1000
                            ff = sorted(f for f in os.listdir(hist_dir) if f.startswith("f_") and f.endswith(".jpg")
                                        and int(f[2:-4]) < _yc)
                            for dead in ff[:600]:
                                try: os.remove(os.path.join(hist_dir, dead))
                                except Exception: pass
                except Exception:
                    pass
                # Retina polish for live stage (after archive so SIM never starves)
                if os.path.getsize(tmp) > 450_000:
                    if _sips_hd_jpeg(tmp, eye):
                        try: os.remove(tmp)
                        except Exception: pass
                    else:
                        try: os.replace(tmp, eye)
                        except Exception: pass
                else:
                    try: os.replace(tmp, eye)
                    except Exception: pass
                globals()["_EYE_PREVIEW_AT"] = time.time()
                _FILM_TIMES.append(now_f)
            else:
                # v947 — never-starve: short timeouts + last-good bridge so FOOTAGE STARVE
                # never drops below ~1fps because a grab hung for 5s
                try:
                    now_f2 = time.time()
                    _due2 = globals().get("_FOOTAGE_DUE", 0.0)
                    if now_f2 >= _due2:
                        # v1195 — the due-gate/advance for this now_f2 slot is paid ONCE here,
                        # up front, so a fresh-grab attempt AND a bridge-last-good fallback can
                        # both try to fill it (_consume_due=False on both archive calls below);
                        # previously the first call's own internal advance silently locked the
                        # second one out of the very slot it was meant to rescue.
                        _iv2 = FOOTAGE_INTERVAL_S
                        globals()["_FOOTAGE_DUE"] = (
                            max(_due2 + _iv2, now_f2 - (_iv2 - 0.01)) if _due2 else now_f2 + _iv2)
                        got = False
                        # v1251 — never-starve must NOT wallpaper the reel with the desktop
                        if _allow_fullscreen_game_fallback("never-starve"):
                            if _grab_full_screen_frame(tmp):
                                got = _archive_footage_copy(tmp, now_f2, why="never-starve-full",
                                                            _consume_due=False)
                                try:
                                    os.replace(tmp, eye)
                                    globals()["_EYE_PREVIEW_AT"] = now_f2
                                except Exception:
                                    pass
                        if not got:
                            # bridge: re-archive last good game frame rather than a hole
                            last = globals().get("_FILM_LAST_GOOD") or (
                                eye if os.path.isfile(eye) else None)
                            if last and os.path.isfile(last):
                                bridged = _archive_footage_copy(last, now_f2, why="bridge-last-good",
                                                                _consume_due=False)
                                if bridged:
                                    globals()["_FOOTAGE_BRIDGES"] = int(globals().get("_FOOTAGE_BRIDGES") or 0) + 1
                except Exception:
                    pass
                try:
                    if os.path.exists(tmp):
                        os.remove(tmp)
                except Exception:
                    pass
        except Exception:
            pass
        dt = time.monotonic() - t0
        time.sleep(max(0.02, FILM_INTERVAL_S - dt))


def start_film_thread():
    global _FILM_THREAD
    if WATCH_MODE or sys.platform != "darwin":
        return
    # v925 LIGHT — the continuous full-screen recorder is the #1 lag; OFF by default. Every
    # actual READ still archives its own frame (per-read hist .jpg), so the SIM retro-debugger
    # keeps a screenshot of every read — just no smooth film between reads. TV_FILM=1 (or the
    # heavy TV_LIGHT=0 / robot mode) brings the cinematic film back for debugging.
    if str(os.environ.get("TV_FILM", "1") or "1").strip().lower() in ("0", "false", "no", "off"):   # v941 — film ON by default (same law as OCR)
        return
    if _FILM_THREAD and _FILM_THREAD.is_alive():
        return
    _FILM_THREAD = threading.Thread(target=_film_loop, daemon=True, name="tv-film")
    _FILM_THREAD.start()


def _d2r_process_alive():
    """v1251 — cheap pgrep for the real game binary (CrossOver-hosted D2R.exe)."""
    try:
        out = subprocess.run(["pgrep", "-f", "D2R.exe"], capture_output=True, timeout=2)
        return out.returncode == 0
    except Exception:
        return False


def _screen_recording_preflight():
    """v1251 — silent TCC check (no dialog). Hot-path safe for film/capture loops."""
    if sys.platform != "darwin":
        return True
    try:
        from Quartz import CGPreflightScreenCaptureAccess
        return bool(CGPreflightScreenCaptureAccess())
    except Exception:
        return True


def _allow_fullscreen_game_fallback(why=""):
    """v1251 — full-screen is ONLY legal when it is actually the game (Metal fullscreen /
    Space transition), never a wallpaper dump of the Mac desktop.

    Blocked when:
      · Screen Recording is denied (Quartz window grab fails; full-screen = desktop)
      · D2R.exe is not running (Battle.net lobby alone is not the game)
    Allowed when SR is OK AND the game process is alive (window unlisted / white Metal)."""
    if not _screen_recording_preflight():
        return False
    if not _d2r_process_alive():
        return False
    return True


def capture_mac(path, timeout=12):
    """Full-screen capture by default (fullscreen D2R / CrossOver).
    Optional TV_CAPTURE=window|auto pins CrossOver/D2R window. v753 hard timeout.
    v779 — always capture to a temp path first (stale-target trust gate killed).
    v1251 — NEVER fall through to full-screen DESKTOP when window pin fails without
    Screen Recording / without a live D2R.exe (Konyo live: eye stuck on wallpaper)."""
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
                # window grab failed — drop stale last-good so we re-list next tick
                _CAP_WHY = "window capture failed (quartz+sc) wid=%s" % wid
                try:
                    # force re-pick next frame (stale wid is the common fail mode)
                    globals()["_PICK_CACHE"] = None
                except Exception:
                    pass
                # v1251 — only fall through to full when the game is truly alive + SR ok
                # (Metal fullscreen). Otherwise HOLD the eye — never wallpaper/desktop.
                if not _allow_fullscreen_game_fallback(_CAP_WHY):
                    _LAST_GOOD_WIN = None
                    _CAP_TARGET = {
                        "mode": "waiting",
                        "label": ("eye held — " + _CAP_WHY +
                                  " · open D2R in-game + grant Screen Recording to Python"),
                        "wid": None,
                    }
                    return False
                _CAP_TARGET = {"mode": "full", "label": "full screen (%s)" % _CAP_WHY,
                               "wid": wid}   # v898 — keep game wid so film still tries D2R.exe
            except Exception as e:
                _CAP_WHY = "window capture exc: %s" % e
                if not _allow_fullscreen_game_fallback(_CAP_WHY):
                    _LAST_GOOD_WIN = None
                    _CAP_TARGET = {"mode": "waiting",
                                   "label": "eye held — %s" % _CAP_WHY, "wid": None}
                    return False
        if mode in ("window", "win", "game"):
            _CAP_TARGET = {"mode": "waiting", "label": "Diablo II / CrossOver not found", "wid": None}
            return False
        # v929.1 (Grok third-eye P0) — AUTO with no window AND no last-good pin must NOT
        # fall through to a full-screen DESKTOP grab: with the v927.5 process-alive gate
        # keeping reads armed, this lane quietly re-created the privacy leak v928.2 closed
        # (desktop frames read + archived while the game window is unlisted). No pin → no eye.
        if not hit:
            # v1251 — process-alive Metal fullscreen exception (window unlisted but D2R.exe up)
            if _allow_fullscreen_game_fallback("no-window-process-alive"):
                _CAP_WHY = "D2R.exe alive · window unlisted — fullscreen game lane"
                # fall through to full-screen grab below
            else:
                _CAP_TARGET = {"mode": "waiting",
                               "label": "D2R window not listed — eye held", "wid": None}
                return False
        # auto with a pinned-but-unGRABbable window → fall through to full screen ONLY when
        # _allow_fullscreen_game_fallback said yes (game owns the display)
    # DEFAULT / fallback: entire display (Quartz first — SC full can also hang under load)
    tmp = _cap_tmp(path)
    try:
        qj = path + ".full.jpg"
        if _quartz_grab_screen(qj, uti="public.jpeg"):
            try:
                subprocess.run(
                    ["sips", "-s", "format", "bmp", qj, "--out", tmp],
                    capture_output=True, timeout=min(8, max(3, timeout)), **NICE_KW)
            except Exception:
                pass
            try:
                if os.path.exists(qj):
                    os.remove(qj)
            except Exception:
                pass
            if _cap_promote(tmp, path, min_bytes=8000):
                _wid_keep = (_CAP_TARGET or {}).get("wid") or (
                    _LAST_GOOD_WIN[0] if _LAST_GOOD_WIN else None)
                _CAP_TARGET = {
                    "mode": "full",
                    "label": ("full screen" + ((" (" + _CAP_WHY + ")") if _CAP_WHY else "")),
                    "wid": _wid_keep,
                }
                return True
        try:
            r = subprocess.run(
                ["screencapture", "-x", "-t", "bmp", tmp],
                capture_output=True, timeout=min(4, timeout), **NICE_KW)
        except Exception:
            r = None
        ok = _cap_promote(tmp, path)
        if ok:
            _wid_keep = (_CAP_TARGET or {}).get("wid") or (
                _LAST_GOOD_WIN[0] if _LAST_GOOD_WIN else None)
            _CAP_TARGET = {
                "mode": "full",
                "label": ("full screen" + ((" (" + _CAP_WHY + ")") if _CAP_WHY else "")),
                "wid": _wid_keep,
            }
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
    """v784/v1419 — Windows capture_win.ps1 writes frames/cap_target.json; surface it on /state.
    utf-8-sig: PowerShell Set-Content -Encoding UTF8 writes a BOM that plain utf-8 json.load can miss,
    leaving UI stuck on default 'eye arming…' while live.png is pure D2R."""
    global _CAP_TARGET
    try:
        p = os.path.join(FRAMES, "cap_target.json")
        if not os.path.isfile(p):
            return
        with open(p, encoding="utf-8-sig") as f:
            raw = f.read()
        if not raw or not raw.strip():
            return
        j = json.loads(raw)
        mode = (j.get("mode") or "full").strip()
        label = (j.get("label") or mode)[:120]
        # Prefer window pin when capture half is healthy
        nxt = {"mode": mode, "label": label, "wid": j.get("wid")}
        if nxt != _CAP_TARGET:
            if mode == "window" and label and (_CAP_TARGET or {}).get("label") != label:
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
HIST_DIR = os.environ.get("TV_HIST") or os.path.join(FRAMES, "hist")   # v886 — ONE hist root, harness-overridable
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
# v1902 — ISOLATED LIKE EVERY OTHER LEARNED FILE. This is WRITTEN (_known_dead_save), and it
# was built from a bare HERE, so a run driven against a fixture hist taught HIS agent the
# fixture's dead frames — permanently, since the whole point of the file is that learning
# survives restarts. Guard the PATH, not the call site.
_KNOWN_DEAD_FILE = (os.environ.get("TV_KNOWN_FRAMES")
                    or os.path.join(_fixture_root(HERE), "known_frames.json"))
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

def _is_real_jpeg(path, min_bytes=32):
    """True only when the file on disk is JPEG SOI magic — not a BMP/PNG renamed .jpg."""
    try:
        if not path or not os.path.isfile(path) or os.path.getsize(path) < min_bytes:
            return False
        with open(path, "rb") as f:
            return f.read(3) == b"\xff\xd8\xff"
    except Exception:
        return False


def _win_image_to_jpeg(src, dest, max_px=1568, quality=80):
    """v1421 — Windows portable JPEG convert via System.Drawing (same stack as capture_win.ps1).
    Zero pip deps. Returns True only when dest is a real JPEG."""
    if sys.platform != "win32" or not src or not os.path.isfile(src):
        return False
    try:
        os.makedirs(os.path.dirname(os.path.abspath(dest)) or ".", exist_ok=True)
        # PowerShell 5.1 + System.Drawing — always present with .NET Framework on Windows desktop.
        # FromFile locks src until Dispose; scale like sips --resampleHeightWidthMax.
        ps = (
            "$ErrorActionPreference='Stop'; "
            "Add-Type -AssemblyName System.Drawing; "
            "$src = $env:TV_JPEG_SRC; $dest = $env:TV_JPEG_DEST; "
            "$max = [int]$env:TV_JPEG_MAX; $q = [int]$env:TV_JPEG_Q; "
            "$img = [System.Drawing.Image]::FromFile($src); "
            "try { "
            "  $w = $img.Width; $h = $img.Height; "
            "  if ($w -gt $max -or $h -gt $max) { "
            "    $scale = [Math]::Min($max / [double]$w, $max / [double]$h); "
            "    $nw = [Math]::Max(1, [int]($w * $scale)); $nh = [Math]::Max(1, [int]($h * $scale)); "
            "    $bmp = New-Object System.Drawing.Bitmap $nw, $nh; "
            "    $g = [System.Drawing.Graphics]::FromImage($bmp); "
            "    $g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic; "
            "    $g.DrawImage($img, 0, 0, $nw, $nh); $g.Dispose(); $img.Dispose(); $img = $bmp; "
            "  } "
            "  $tmp = $dest + '.part.jpg'; "
            "  $codec = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | "
            "    Where-Object { $_.MimeType -eq 'image/jpeg' } | Select-Object -First 1; "
            "  $ep = New-Object System.Drawing.Imaging.EncoderParameters 1; "
            "  $ep.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter "
            "    ([System.Drawing.Imaging.Encoder]::Quality, [long]$q); "
            "  $img.Save($tmp, $codec, $ep); "
            "  if (Test-Path -LiteralPath $dest) { Remove-Item -LiteralPath $dest -Force -EA SilentlyContinue }; "
            "  Move-Item -LiteralPath $tmp -Destination $dest -Force; "
            "} finally { try { $img.Dispose() } catch {} }"
        )
        env = os.environ.copy()
        env["TV_JPEG_SRC"] = os.path.abspath(src)
        env["TV_JPEG_DEST"] = os.path.abspath(dest)
        env["TV_JPEG_MAX"] = str(int(max_px))
        env["TV_JPEG_Q"] = str(int(max(40, min(95, quality))))
        r = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", ps],
            capture_output=True, timeout=25, env=env,
            **{k: v for k, v in (NICE_KW.items() if isinstance(globals().get("NICE_KW"), dict) else {})
               if k in ("creationflags", "start_new_session")})
        return r.returncode == 0 and _is_real_jpeg(dest)
    except Exception:
        return False


def _to_jpeg(src, dest, max_px=1568, quality=80):
    """Mac sips first; Windows System.Drawing; never claim success on non-JPEG bytes.

    v1450 — sips --resampleHeightWidthMax UPSAMPLES small sources on current macOS
    (48px → max_px). Only pass the flag when the source actually exceeds max_px (downscale)."""
    if not src or not os.path.isfile(src):
        return False
    # Already a real JPEG and dest==src path intent — copy if needed.
    if _is_real_jpeg(src) and os.path.abspath(src) == os.path.abspath(dest):
        return True
    if _is_real_jpeg(src) and max(os.path.getsize(src), 1) < 2_500_000:
        try:
            import shutil
            os.makedirs(os.path.dirname(os.path.abspath(dest)) or ".", exist_ok=True)
            # still downscale oversized JPEGs (big eye frames) when max_px set
            w, h = _sips_pixel_size(src)
            if max_px and w and h and max(w, h) > int(max_px):
                pass  # fall through to sips convert+downsample
            else:
                shutil.copy2(src, dest)
                return _is_real_jpeg(dest)
        except Exception:
            pass
    try:
        os.makedirs(os.path.dirname(os.path.abspath(dest)) or ".", exist_ok=True)
        cmd = ["sips", "-s", "format", "jpeg", "-s", "formatOptions", str(int(quality))]
        w, h = _sips_pixel_size(src)
        if max_px and w and h and max(w, h) > int(max_px):
            cmd += ["--resampleHeightWidthMax", str(int(max_px))]
        elif max_px and not (w and h):
            # unknown dims — only resample when source file is large enough to need it
            try:
                if os.path.getsize(src) > 400_000:
                    cmd += ["--resampleHeightWidthMax", str(int(max_px))]
            except Exception:
                pass
        cmd += [src, "--out", dest]
        r = subprocess.run(cmd, capture_output=True, timeout=25, **NICE_KW)
        if r.returncode == 0 and _is_real_jpeg(dest):
            return True
    except Exception:
        pass
    if _win_image_to_jpeg(src, dest, max_px=max_px, quality=quality):
        return True
    return False


def _readable_frame(ap, out_jpg=None):
    """v710.6 LIVE-SESSION FIX (Konyo's first real run): claude's Read tool chokes on a 16MB
    raw BMP — both live reads timed out at 180s. Convert to a 1568px JPEG (the locked intake
    spec) before the vision call. Mac: sips. Windows v1421: System.Drawing (not live.png alone —
    PNG can still be multi-MB and some readers expect JPEG). Falls back to live.png then original."""
    try:
        if not ap.lower().endswith(".bmp"):
            return ap
        jp = out_jpg or os.path.join(FRAMES, "read.jpg")
        if _to_jpeg(ap, jp, max_px=1568, quality=80):
            global _JPEG_LOGGED
            if not globals().get("_JPEG_LOGGED"):
                _JPEG_LOGGED = True
                try:
                    was = os.path.getsize(ap)
                    now = os.path.getsize(jp)
                    ev("boot", "vision transport OK — frame \u2192 read.jpg %dKB (was %dMB)"
                       % (now // 1024, max(1, was // 1024 // 1024)))
                except Exception:
                    pass
            return jp
        # v1709 — do NOT substitute frames/eye.jpg. That is a DIFFERENT photo
        # (the live eye, not this settle frame). A convert-fail returns the
        # original path — honest BMP passthrough — never another file's pixels.
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
                                # v940.4 — shield the BASE jpeg too. Verify journals
                                # frameId 'N_ts#v' but the file is always 'N_ts.jpg';
                                # protecting only 'N_ts#v.jpg' left the real photo killable.
                                base = str(fid).split("#", 1)[0]
                                ids.add(str(fid) + ".jpg")
                                if base:
                                    ids.add(base + ".jpg")
                                    # reel-relative ids: reel_<sid>/f_<ts>
                                    if "/" in base:
                                        ids.add(os.path.basename(base) + ".jpg")
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
    Keeps last HIST_KEEP files. Never raises into the scan loop.

    v1421 Windows truth: the old portable fallback copied live.bmp bytes into a .jpg name
    (magic 42 4D). Claude Read + Theatre then choked on multi-MB BMP-as-jpg (70–180s reads).
    Archive MUST land real JPEG SOI (FF D8 FF) — convert via sips/System.Drawing, else copy
    eye.jpg / read.jpg, never a raw BMP body under a .jpg name when a real JPEG path exists."""
    ts_ms = ts_ms if ts_ms is not None else int(time.time() * 1000)
    fid = "%d_%d" % (int(n), int(ts_ms))
    try:
        os.makedirs(HIST_DIR, exist_ok=True)
        dest = os.path.join(HIST_DIR, fid + ".jpg")
        src = os.path.abspath(src_path) if src_path else ""
        ok = False
        if src and os.path.isfile(src):
            # Prefer full capture → HIST_MAX_PX JPEG for human eyes (AI path stays 1568 via _readable_frame)
            if src.lower().endswith((".bmp", ".png", ".jpg", ".jpeg")):
                ok = _to_jpeg(src, dest, max_px=HIST_MAX_PX, quality=82)
            if not ok:
                # portable fallback #1: the vision JPEG (already converted+downscaled)
                jp = os.path.join(FRAMES, "read.jpg")
                if _is_real_jpeg(jp):
                    import shutil
                    shutil.copy2(jp, dest)
                    ok = _is_real_jpeg(dest)
            if not ok:
                # portable fallback #2: capture film eye (always real JPEG from capture_win)
                eye = os.path.join(FRAMES, "eye.jpg")
                if _is_real_jpeg(eye):
                    import shutil
                    shutil.copy2(eye, dest)
                    ok = _is_real_jpeg(dest)
            if not ok:
                # portable fallback #3: live.png → JPEG convert (Windows capture twin)
                png = os.path.join(FRAMES, "live.png")
                if os.path.isfile(png):
                    ok = _to_jpeg(png, dest, max_px=HIST_MAX_PX, quality=82)
            if not ok:
                # last resort: raw copy ONLY if source is already JPEG; never plant BMP as .jpg
                if _is_real_jpeg(src):
                    try:
                        import shutil
                        shutil.copy2(src, dest)
                        ok = _is_real_jpeg(dest)
                    except Exception:
                        ok = False
                elif src.lower().endswith(".png") and os.path.isfile(src):
                    # PNG body behind .jpg name still renders in browsers (legacy v755.3)
                    try:
                        import shutil
                        shutil.copy2(src, dest)
                        ok = os.path.isfile(dest) and os.path.getsize(dest) > 32
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
                # v883 — REELS DIE WHOLE, LAST: if loose shedding still can't breathe, retire
                # the OLDEST sealed reels in one piece (a run keeps its full video or is gone —
                # never a half-eaten reel).
                try:
                    reels = sorted(d2 for d2 in os.listdir(HIST_DIR) if d2.startswith("reel_"))
                    if len(reels) > 2 and not foot_files:   # loose pool empty → oldest whole reel goes
                        import shutil as _shr
                        _shr.rmtree(os.path.join(HIST_DIR, reels[0]), ignore_errors=True)
                except Exception:
                    pass
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

def _resolve_read_ts(cap_ts_override=None):
    """v1187 — captureTs join law: the timestamp stamped into a read's frame_id/captureTs must
    be the FRAME's actual capture clock, never the moment a caller got around to reading it
    (same law as the intake-result A0 fix above: 'retro joins on captureTs, never receipt
    time'). A queue/backlog drain (_fire_read's settle-queue / text-eye-sweep-* origins) reads
    a snapshot captured EARLIER — held while readers were busy, up to SETTLE_QUEUE_STALE_MS —
    so it must pass that entry's own tracked capture clock as cap_ts_override. A fresh/live read
    has no earlier clock to report, so it falls back to now()."""
    return int(cap_ts_override) if cap_ts_override else int(time.time() * 1000)


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

# v948.17 — Grok P1-5 (2026-07-21 fast-run soak): claude_read()'s warm ask() used the
# VisionWorker default (timeout=75) and its one-shot fallback used 90s — a single frame
# (a scene-transition still) legitimately took 68,978ms and, with POOL_N=1 outside robot
# mode, that one read holds the ENTIRE live lane hostage (no new live read, no idle-gap
# second-eye sweep) for up to 75+90=165s worst case. Per the Master Brain law ("a 66s live
# stall is a signal to route to retro, not a failure" — ENGINE_ARCHITECTURE.md §Master Brain
# law a), cap a single live read's in-flight time much tighter: every named read this soak
# finished in 9-15s, so a generous-but-bounded ceiling lets the lane free up and hand the
# frame to the retro/KAI layers instead of blocking on an outlier. TV_LIVE_READ_TIMEOUT_S
# overrides for tuning; genius-escalate (a secondary, capped, optional pass) is untouched.
try:
    LIVE_READ_TIMEOUT_S = max(5.0, float(os.environ.get("TV_LIVE_READ_TIMEOUT_S", "35") or 35))
except Exception:
    LIVE_READ_TIMEOUT_S = 35.0

# v720 — AUTH PATH FIX (live run #2): if ANTHROPIC_API_KEY (or sibling API tokens) is set in
# the shell, every headless `claude -p` prefers that key over the user's Claude subscription
# login. A dead/rate-limited key hangs past 40–90s with empty stdout — exactly run #2's
# warm + oneshot timeouts. Strip API-key auth so vision rides the *logged-in* claude plan
# (the product contract: "your subscription, not API keys"). Keep OAuth tokens if present.
# v879 (army §2) — EVERY helper subprocess yields to the game. Mac/Linux: nice(10) via
# preexec_fn. Windows: BELOW_NORMAL_PRIORITY_CLASS folded into creationflags.
if sys.platform == "win32":
    NICE_KW = {"creationflags": 0x4000}   # BELOW_NORMAL_PRIORITY_CLASS
else:
    NICE_KW = {"preexec_fn": (lambda: os.nice(10))}

_API_AUTH_ENV = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")
def _claude_env():
    """Env for vision subprocesses: subscription login, not shell API keys."""
    env = os.environ.copy()
    stripped = [k for k in _API_AUTH_ENV if env.pop(k, None) is not None]
    # v1379 — agent-teams auto mode must never ride vision children (subscription burn)
    env.pop("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS", None)
    return env, stripped

def _log_auth_once(stripped):
    if not stripped or globals().get("_AUTH_LOGGED"):
        return
    globals()["_AUTH_LOGGED"] = True
    ev("boot", f"vision auth: stripped {','.join(stripped)} — using Claude subscription login")

# v1379 LEAK FIX — every cold/warm `claude -p` used to inherit cwd=d2r_bible_tests + full
# project settings (CLAUDE.md, agent teams, high effort). Each screenshot became a
# ~1.3MB Claude Code session with 20k+ cache tokens. Lean args skip project context, do
# not persist sessions, keep effort low, and ALWAYS pin --model so the global Claude
# default (fable in ~/.claude/settings.json) never hijacks vision. Product model = sonnet.
# Auth stays subscription OAuth (not --bare).
_VISION_CWD = os.environ.get("TV_VISION_CWD") or os.path.join(tempfile.gettempdir(), "tvd-vision-cwd")
try:
    os.makedirs(_VISION_CWD, exist_ok=True)
except Exception:
    _VISION_CWD = tempfile.gettempdir()

def _vision_model(model=None):
    """Pin vision to sonnet (product). Never allow empty/fable to inherit user settings."""
    m = str(model or FAST_MODEL or "sonnet").strip() or "sonnet"
    lo = m.lower()
    if "fable" in lo:
        return "sonnet"
    return m

def _argv_seam(env_name, default):
    """v1461 — optional JSON-list override for a spawn's argv PREFIX. Unset => `default`.

    TV_CLAUDE_BIN / TV_OCR_BIN hold a single executable PATH, which cannot express "run this
    script under THIS interpreter". The suites' fakes are .py files: on the Mac a shebang
    makes them directly executable, but on Windows a bare .py is not a valid CreateProcess
    image ([WinError 193] %1 is not a valid Win32 application), so every fake-worker test
    failed there. Wrapping the fake in a .cmd is NOT a fix: it inserts an extra process that
    survives p.kill(), leaving the real child orphaned on the pipe — which is precisely the
    leak the v1204/v1206 shutdown tests exist to catch, and it hangs them.

    So allow the prefix itself to be a list, exactly as _ocr_worker_cmd already does for the
    Windows OCR lane (powershell + .ps1). Production never sets these, so behaviour is
    byte-identical; only the suites do.
    """
    raw = os.environ.get(env_name)
    if raw:
        try:
            v = json.loads(raw)
            if isinstance(v, list) and v:
                return [str(x) for x in v]
        except Exception:
            pass
    return list(default)


def _claude_lean_args(model, *, stream=False, add_dirs=None):
    """CLI argv for vision/intake calls that must not load the monorepo project."""
    args = _argv_seam("TV_CLAUDE_ARGV", [CLAUDE_BIN]) + ["-p"]
    if stream:
        args += ["--input-format", "stream-json", "--output-format", "stream-json", "--verbose"]
    else:
        args += ["--output-format", "text"]
    args += [
        "--model", _vision_model(model),
        "--allowedTools", "Read",
        "--strict-mcp-config",
        "--no-session-persistence",
        "--setting-sources", "user",
        "--effort", os.environ.get("TV_VISION_EFFORT", "low") or "low",
    ]
    for d in (add_dirs or []):
        if d and os.path.isdir(d):
            args += ["--add-dir", d]
    return args

# v1379 — hard subscription circuit breaker for cold oneshots + warm budget log.
# Armed only for REAL claude CLI vision — never for TV_STUB / fake_claude (tests would
# burn the hourly cap on themselves and return None without spawning a worker).
def _sub_budget_path():
    """Where the subscription meter lives — and never HIS meter when the world is a fixture.

    v1869 — MEASURED: one full 32-gate run spends ONE REAL VISION CALL against his subscription and
    writes it into this file. Every push runs those gates, so every push quietly bought a read he
    did not ask for. Small; unasked; and the meter is the one thing that must describe his account
    and nothing else.

    Same rule as the journal (v1867), for the same reason: a caller that isolates TV_HIST has said
    "this is not his world", and a meter counting reads made in a fixture is not a meter of his
    account. TV_SUB_BUDGET wins when named explicitly. [[feedback-fixtures-never-touch-live-data]]
    """
    explicit = os.environ.get("TV_SUB_BUDGET")
    if explicit:
        return explicit
    hist = os.environ.get("TV_HIST")
    if hist:
        try:
            h = os.path.realpath(hist)
            if not _under(hist, HERE):
                return os.path.join(h, ".subscription_budget.json")
        except Exception:
            pass
    return os.path.join(HERE, ".subscription_budget.json")


_SUB_BUDGET_PATH = _sub_budget_path()
# v1777 — THE CAPS WERE SIZED FOR A LIVE SESSION, NOT FOR READING HIS FOOTAGE BACK.
# 60/hour and 250/day fit a farm session sipping the odd frame. A Chronicle catch-up is the opposite
# shape: ONE reel of his thorough scroll is ~290 pages, so the very first honest sweep could not fit
# inside a day's allowance — and because a capped read used to answer scene='gameplay' instead of
# refusing (fixed below), it looked like his footage was empty rather than like the meter was full.
# Measured tonight: 250/250 at 01:00, every read returning in 0.0s with nothing, for hours.
#
# Raised to 4000/hour and 20000/day. These are OUR OWN guard rails, not Anthropic's — they exist so
# a runaway loop cannot spend his subscription unattended, and that job is done just as well by a
# number that does not also block the one workload the feature exists for. The REAL pace limit is
# the throttle detector (_note_slot_death), which watches actual worker deaths and is untouched.
try:
    _SUB_HOURLY_MAX = max(0, int(os.environ.get("TV_VISION_HOURLY_MAX", "4000") or 4000))
except Exception:
    _SUB_HOURLY_MAX = 4000
try:
    _SUB_DAILY_MAX = max(0, int(os.environ.get("TV_VISION_DAILY_MAX", "20000") or 20000))
except Exception:
    _SUB_DAILY_MAX = 20000
_sub_budget_lock = threading.Lock()


def _sub_budget_load():
    """v1472 — read the subscription-budget file WITHOUT leaking a handle.

    The two call sites used a bare `open(...).read()`, which relies on refcount GC to close.
    This runs on every vision read, so during a long farm session it churns thousands of
    handles — and on Windows an open handle also blocks replacing the file underneath it.
    """
    try:
        if not os.path.isfile(_SUB_BUDGET_PATH):
            return {}
        with open(_SUB_BUDGET_PATH, encoding="utf-8") as fh:
            return json.loads(fh.read()) or {}
    except Exception:
        return {}

def _vision_budget_armed():
    """True only when a real subscription-costing Claude binary is in play.

    v1463 — judge the argv that is ACTUALLY SPAWNED, not just CLAUDE_BIN. v1461 added the
    TV_CLAUDE_ARGV seam, which decides the real command, while this guard still read only
    CLAUDE_BIN's basename — so the two could disagree: TV_CLAUDE_BIN=.../fake_claude.py with
    TV_CLAUDE_ARGV=["claude"] disarmed the hourly/daily subscription cap while every spawn was
    the real CLI burning real quota. Fail SAFE: the circuit stays armed unless the thing being
    executed is genuinely a fake.
    """
    if os.environ.get("TV_STUB") or os.environ.get("TV_NO_BUDGET") == "1":
        return False
    try:
        argv = _argv_seam("TV_CLAUDE_ARGV", [CLAUDE_BIN])
    except Exception:
        argv = [CLAUDE_BIN]
    try:
        blob = " ".join(os.path.basename(str(a or "")).lower() for a in argv)
    except Exception:
        blob = ""
    if "fake_claude" in blob:
        return False
    return True

def _sub_budget_calls(st, now):
    """The call timestamps that still count, in SECONDS, with nonsense dropped.

    v1868 — HIS LIVE BUDGET FILE HELD A MILLISECOND TIMESTAMP AMONG SECONDS. Measured:
    1787177667153.0 sitting in `calls` beside 404 ordinary seconds-scale entries. Both filters here
    are written as `now - t < WINDOW`, and for a value ~55,000 years in the future that difference
    is hugely NEGATIVE — so it passes every window, forever. One permanent slot off the hourly cap
    AND the daily cap, invisible, and it can never age out on its own.

    Harmless at 4000/hour and 20000/day; not harmless as a mechanism, and not new — this is the same
    unit collision already recorded against the G5 lane. A meter that cannot be corrected by the
    passage of time is a meter that only ever goes one way.

    So: a value that looks like milliseconds IS milliseconds (nothing in 2026 is 1.7e12 seconds), a
    value in the future beyond a minute of clock skew is dropped rather than trusted, and the window
    is a two-sided one — `0 <= now - t < WINDOW` — because "not older than a day" and "not in the
    future" are two conditions and the one-sided test only ever checked one of them.
    [[d2r-g5-budget-unit-collision]] [[unknown-stays-unknown]]
    """
    out = []
    for raw in (st.get("calls") or []):
        try:
            t = float(raw)
        except Exception:
            continue
        if t > 1e12:            # milliseconds, written by something that used a different clock
            t = t / 1000.0
        if t > now + 60:        # beyond clock skew: a timestamp we cannot place, not a call
            continue
        if now - t < 86400:
            out.append(t)
    return out


def _sub_budget_check(kind="vision"):
    """Return None if allowed, else a short reason string (circuit open)."""
    if not _vision_budget_armed():
        return None
    if _SUB_HOURLY_MAX <= 0 or _SUB_DAILY_MAX <= 0:
        return "subscription circuit open (TV_VISION_*_MAX=0)"
    now = time.time()
    with _sub_budget_lock:
        try:
            st = _sub_budget_load()   # v1472 — was a bare open().read(); the vision lane hits this
                                      # on EVERY read, so the leaked handle recurred per frame
        except Exception:
            st = {}
        calls = _sub_budget_calls(st, now)
        hour = [t for t in calls if now - t < 3600]
        if len(hour) >= _SUB_HOURLY_MAX:
            return "subscription hourly cap %d/%d (%s)" % (len(hour), _SUB_HOURLY_MAX, kind)
        if len(calls) >= _SUB_DAILY_MAX:
            return "subscription daily cap %d/%d (%s)" % (len(calls), _SUB_DAILY_MAX, kind)
        return None

def _sub_budget_record():
    if not _vision_budget_armed():
        return
    now = time.time()
    with _sub_budget_lock:
        try:
            st = _sub_budget_load()   # v1472 — was a bare open().read(); the vision lane hits this
                                      # on EVERY read, so the leaked handle recurred per frame
        except Exception:
            st = {}
        calls = _sub_budget_calls(st, now)   # v1868 — normalise on WRITE too, or the poison is
        calls.append(now)                    # simply rewritten every time a read is recorded
        try:
            # v1779 — ATOMIC, because a torn write here silently DISARMS the circuit breaker.
            # _sub_budget_load returns {} on any parse failure, so a half-written file makes the
            # cap restart from zero with no message anywhere — the guard protecting his account
            # fails OPEN. The file is rewritten on every vision read and holds up to _SUB_DAILY_MAX
            # timestamps, so an interrupted sweep is a realistic way to get there. Every other state
            # file in this lane already uses tmp+replace; this one was missed. Found by review.
            _tmp = _SUB_BUDGET_PATH + ".tmp"
            with open(_tmp, "w", encoding="utf-8") as _bf:
                _bf.write(json.dumps({"calls": calls, "last": now}))
                _bf.flush()
                try:
                    os.fsync(_bf.fileno())
                except Exception:
                    pass
            os.replace(_tmp, _SUB_BUDGET_PATH)
        except Exception:
            pass

class VisionWorker:
    def __init__(self, model=None):
        # v720.1 — lock: warm thread + settle-read must never interleave on one stream
        self.model = model or FAST_MODEL
        self.p = None; self.q = None; self.turns = 0; self.lock = threading.Lock()
    def _spawn(self):
        import queue
        env, stripped = _claude_env()
        _log_auth_once(stripped)
        # Allow Read on frames + hist so absolute paths resolve even with empty vision cwd
        add = [FRAMES]
        hist = os.path.join(FRAMES, "hist")
        if os.path.isdir(hist):
            add.append(hist)
        self.p = subprocess.Popen(
            _claude_lean_args(self.model, stream=True, add_dirs=add),
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, bufsize=1, env=env, cwd=_VISION_CWD,
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
        blocked = _sub_budget_check("warm")
        if blocked:
            try:
                ev("cap", blocked)
            except Exception:
                pass
            return None
        with self.lock:
            try:
                if self.p is None or self.p.poll() is not None or self.turns >= WORKER_MAX_TURNS:
                    self.stop(); self._spawn()
                msg = {"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": prompt}]}}
                self.p.stdin.write(json.dumps(msg) + "\n"); self.p.stdin.flush()
                # v1200 — monotonic, not wall-clock: this deadline is the LITERAL enforcement of
                # LIVE_READ_TIMEOUT_S, the Master Brain law rounds 1-4 all protected from other
                # angles. time.time() can jump BACKWARD (NTP resync on sleep/wake — routine over
                # a multi-hour session, same class engine-capture just fixed in _film_loop
                # v1199); mid-read, that makes `deadline - time.time()` balloon to the size of
                # the jump, so `self.q.get(timeout=...)` blocks for however long the clock
                # jumped — reintroducing the exact "hang the entire live lane" failure this whole
                # arc exists to eliminate, in the ONE place that's supposed to guarantee it can't.
                deadline = time.monotonic() + timeout
                while time.monotonic() < deadline:
                    try: line = self.q.get(timeout=max(0.1, deadline - time.monotonic()))
                    except Exception: break
                    if line is None: break
                    line = line.strip()
                    if not line: continue
                    try: j = json.loads(line)
                    except Exception: continue
                    if j.get("type") == "result":
                        self.turns += 1
                        _sub_budget_record()
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
    """v900 — pool fits the MACHINE (Konyo: 4 workers made MacBook + CrossOver unplayable).
    ≤16GB → 2 · 17–31GB → 3 · ≥32GB → 4. TV_POOL always wins (max 6)."""
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
    if gb >= 32:
        return 4
    if gb >= 20:
        return 3
    return 2


_TP_ENV = os.environ.get("TV_POOL", "").strip()
if ROBOT_MODE:
    POOL_N = max(1, min(6, int(_TP_ENV))) if _TP_ENV else max(1, min(6, _pool_default()))
else:
    # v901 Auto Intake: ONE Claude always. TV_POOL ignored unless TV_ROBOT=1 (Robot frozen).
    POOL_N = 1
ORDER_HOLD_MS = max(5000, int(os.environ.get("TV_ORDER_HOLD_MS", "20000" if not ROBOT_MODE else "45000") or 20000))
_WORKERS = [_WORKER] + [VisionWorker() for _ in range(max(0, POOL_N - 1))]
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
    """v900 — lean concurrent heartbeats. Pool 2 machines stay at 1 in-flight heartbeat so
    Claude + capture never thrash D2R. Bigger pools can earn 2."""
    hi = max(1, POOL_N // 2)
    if _is_throttled():
        return 1
    fps = _foot_fps_now()
    cap_ms = globals().get("_FILM_CAP_MS") or 0
    if (fps is not None and fps < 0.6) or cap_ms > 800:
        return 1
    if POOL_N >= 3 and fps is not None and fps >= 0.9 and cap_ms < 250:
        return min(hi, 2)
    return 1


def _heartbeat_in_flight_n():
    with _pool_lock:
        return sum(1 for j in _in_flight.values() if j.get("origin") == "heartbeat")


# v1576 — `_heartbeat_in_flight()` (a bare `_heartbeat_in_flight_n() > 0` wrapper) was removed:
# zero callers repo-wide; the one live consumer (the ROBOT_MODE heartbeat gate) counts with
# `_heartbeat_in_flight_n() < _heartbeat_cap()` and never asked the boolean question.


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
    """Return `rid` to the free list. v948.17 — sentinel/override ids (e.g. the stall-drain
    worker's negative _STALL_RID) are never pool members and must never leak in here; a real
    pool slot is always in range(POOL_N)."""
    with _pool_lock:
        if rid is None or rid < 0:
            return
        if rid not in _pool_free:
            _pool_free.append(rid)
            _pool_free.sort()


# ── v948.17 STALL-DRAIN — a PARALLEL second-eye worker for a hung live lane (Grok P1-4,
# 2026-07-21 fast-run soak). Outside ROBOT_MODE, POOL_N==1 by design ("ONE Claude always"),
# so the old second-eye sweep gate (`_vision_in_flight_n() < POOL_N`) can NEVER open while
# the single live reader is busy — even when that read has been stuck in flight for a minute.
# A hung live read is not an "idle gap"; it's exactly the case the backlog most needs draining
# in. This dedicated worker lives entirely OUTSIDE POOL_N/_pool_free bookkeeping (sentinel
# reader id _STALL_RID, never returned to `_pool_free`) so it can never be claimed by ordinary
# live dispatch and never steals the "one Claude" live slot — it only ever fires the bounded,
# already-captured backlog sweep while the live eye is demonstrably stalled.
_STALL_RID = -1                 # sentinel reader id — always outside range(POOL_N)
_STALL_WORKER = None
_STALL_BUSY = False
STALL_DRAIN_S = max(1.0, float(os.environ.get("TV_STALL_DRAIN_S", "20") or 20))


def _stall_worker():
    """Lazily-created, dedicated VisionWorker for stall-drain sweeps only — never shared
    with the live reader pool, so a hung live subprocess can't also silence this one."""
    global _STALL_WORKER
    if _STALL_WORKER is None:
        _STALL_WORKER = VisionWorker()
    return _STALL_WORKER


def _live_stall_ms():
    """Age (ms) of the OLDEST in-flight read, or 0 if the pool is idle. Used to detect a
    genuinely hung live read (not just a normal-length one) before parallel-draining."""
    with _pool_lock:
        if not _in_flight:
            return 0
        oldest = min(int(j.get("startedAt") or 0) for j in _in_flight.values())
    return max(0, int(time.time() * 1000) - oldest) if oldest else 0


def _stall_drain_decision(backlog_len, in_flight_n, pool_n, stall_ms, stall_busy,
                           enabled=True, threshold_ms=None):
    """PURE decision (Grok P1-4 pin target) — fire the parallel stall-drain sweep only when:
      • the feature is enabled;
      • the backlog actually has something piling up (backlog_len > 0);
      • the live pool is FULLY busy (in_flight_n >= pool_n) — when a slot is free the ordinary
        '< POOL_N' idle-gap sweep already covers it, no need for a second worker;
      • the oldest in-flight read has been running >= threshold_ms — a genuine stall, not an
        ordinary 9-15s named read;
      • no stall-sweep is already running (bounded to exactly one parallel sweep at a time).
    """
    if not enabled:
        return False
    if stall_busy:
        return False
    if backlog_len <= 0:
        return False
    if in_flight_n < pool_n:
        return False
    thr = (STALL_DRAIN_S * 1000.0) if threshold_ms is None else float(threshold_ms)
    return float(stall_ms) >= thr


def _stall_drain_ready():
    """Thin glue over `_stall_drain_decision` reading the live globals."""
    return _stall_drain_decision(
        backlog_len=_text_eye_backlog_len(),
        in_flight_n=_vision_in_flight_n(),
        pool_n=POOL_N,
        stall_ms=_live_stall_ms(),
        stall_busy=globals().get("_STALL_BUSY", False),
        enabled=os.environ.get("TV_STALL_DRAIN", "1") != "0",
    )


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
                journal_skip("order-straggler", "applied out of order after hold")   # v880 A2.8
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
# v899 — farewell/pool join hard-cap (was 90s; 400-read desktop sessions hung SIGNING OFF forever)
# v925 LIGHT — shorter cap; the farewell VISION read is OFF by default now (see close_session):
# it was the "END SESSION stuck" bug — a final Claude read stacked on pool-join + flush + fold
# past the console's ~22s wait. LIGHT END = seal the reel and exit, instant, no vision call.
FAREWELL_MAX_S = max(3.0, min(45.0, float(os.environ.get("TV_FAREWELL_S", "6") or 6)))
FAREWELL_READ_ON = str(os.environ.get("TV_FAREWELL", "0" if LIGHT_MODE else "1")).strip().lower() in ("1", "true", "yes", "on")


def _pool_shutdown(timeout=None, keep_worker0=True):
    """v864/v899 — join in-flight briefly, then inert late threads. Hard-capped (default ~12s).
    v1200 — `deadline` here is monotonic (see the `_verify_drain` note below): a shutdown that
    straddles a backward wall-clock jump must not join in-flight reads for the length of the
    jump instead of FAREWELL_MAX_S.

    v1206 — `keep_worker0`: Worker 0 (`_WORKER`) is exempted from the stop sweep below ONLY
    because farewell_read() needs it warm right after this call returns (v863: 'Worker 0 ==
    _WORKER, the farewell / POOL_N=1 fast path'). But v925 LIGHT made the farewell vision read
    OPT-IN — FAREWELL_READ_ON defaults False outside ROBOT_MODE — so in Konyo's actual default
    config `close_session` never runs a farewell read at all, and `_WORKER`'s warm `claude -p`
    child was NEVER being stopped by anything: close_session ends in os._exit(0) right after,
    same orphan-process leak as the round-6 stall-worker fix, except this sibling leaks on
    EVERY session close instead of only when the stall-drain safety net fires. The caller
    (`close_session`) knows by this point whether a real farewell read is actually coming —
    pass keep_worker0=False whenever it isn't, and worker 0 gets swept too."""
    if timeout is None:
        timeout = FAREWELL_MAX_S
    globals()["_POOL_STOPPING"] = True
    deadline = time.monotonic() + max(0.0, float(timeout))
    while time.monotonic() < deadline:
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
    # v1179 CLOSER — a verify job for the last read(s) of the session was silently dropped when
    # the process exited with `_VERIFY_Q` non-empty (nothing ever drains it but the main loop's
    # idle gap, which a closing session no longer reaches). That item's second-look correction
    # then never runs at all — a silent starve, not an honest miss. Spend only what's LEFT of
    # this function's own `deadline` (never extends shutdown time): if the in-flight join above
    # finished early, as it usually does, there's a few spare seconds to spend here instead of
    # going idle; if it already ate the whole budget, `time.monotonic() < deadline` is false and
    # this is a no-op.
    try:
        if VERIFY_ON and _VERIFY_Q and time.monotonic() < deadline:
            _verify_drain(worker=_WORKER, budget=len(_VERIFY_Q),
                          timeout=max(3.0, deadline - time.monotonic()), deadline=deadline)
    except Exception:
        pass
    for w in _WORKERS[1:]:
        try: w.stop()
        except Exception: pass
    if not keep_worker0:
        try: _WORKER.stop()
        except Exception: pass
    # v1204 — the stall-drain worker (`_stall_worker()`) is a SEPARATE VisionWorker deliberately
    # kept OUTSIDE _WORKERS/_pool_free (never claimed by ordinary live dispatch — see the
    # v948.17 STALL-DRAIN block above), so a hung live reader can never also silence it. That
    # also means it's outside THIS sweep: if the stall-drain safety net ever fired even once
    # this session, its warm `claude -p` child (a ~200-600MB subprocess, same as any pool
    # worker) is a genuine ORPHAN at shutdown — close_session ends in os._exit(0), which skips
    # __del__/atexit entirely, so nothing else was ever going to kill it. Stop it here too, only
    # if it was ever actually created (the common case: the stall-drain path never fired).
    _sw = globals().get("_STALL_WORKER")
    if _sw is not None:
        try: _sw.stop()
        except Exception: pass
    # v1206 — a second sibling: `_OCR` (the persistent OcrWorker behind the fast/text-eye lane)
    # is likewise never stopped anywhere in the file. Unlike `_WORKER`, it has no "keep it warm
    # for farewell" reason to survive shutdown — farewell_read() explicitly skips OCR ("deep
    # only — farewell must land; OCR is optional and can wait") — so it's always safe to stop.
    try: _OCR.stop()
    except Exception: pass


def _win_d2r_process_alive():
    """v1413/v1414 — Windows: is D2R.exe running?
    v1414: NEVER use tasklist (hangs under D2R load and freezes the agent/UI).
    Prefer cap_target.json from capture_win, then Win32 process snapshot."""
    if not sys.platform.startswith("win"):
        return False
    # 1) capture half already wrote the truth (no process scan)
    try:
        tp = os.path.join(FRAMES, "cap_target.json")
        if os.path.isfile(tp):
            with open(tp, encoding="utf-8") as f:
                j = json.load(f) or {}
            if j.get("d2rProcess") is True:
                return True
            lab = str(j.get("label") or "").lower()
            mode = str(j.get("mode") or "").lower()
            if mode == "window" and ("d2r" in lab or "diablo" in lab):
                return True
    except Exception:
        pass
    # 2) Toolhelp32 snapshot (no tasklist.exe)
    try:
        import ctypes
        from ctypes import wintypes
        TH32CS_SNAPPROCESS = 0x00000002
        class PROCESSENTRY32W(ctypes.Structure):
            _fields_ = [
                ("dwSize", wintypes.DWORD),
                ("cntUsage", wintypes.DWORD),
                ("th32ProcessID", wintypes.DWORD),
                ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
                ("th32ModuleID", wintypes.DWORD),
                ("cntThreads", wintypes.DWORD),
                ("th32ParentProcessID", wintypes.DWORD),
                ("pcPriClassBase", ctypes.c_long),
                ("dwFlags", wintypes.DWORD),
                ("szExeFile", wintypes.WCHAR * 260),
            ]
        k32 = ctypes.windll.kernel32
        snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if snap == ctypes.c_void_p(-1).value or snap == -1:
            return False
        try:
            pe = PROCESSENTRY32W()
            pe.dwSize = ctypes.sizeof(PROCESSENTRY32W)
            if not k32.Process32FirstW(snap, ctypes.byref(pe)):
                return False
            while True:
                n = (pe.szExeFile or "").lower()
                if n in ("d2r.exe",) or n.startswith("d2r") or "diabloii" in n.replace(" ", ""):
                    return True
                if not k32.Process32NextW(snap, ctypes.byref(pe)):
                    break
        finally:
            k32.CloseHandle(snap)
    except Exception:
        pass
    return False


def _game_window_present():
    """v899 — True when the real D2R game window is pin-able (Mac Quartz / Win watch target).
    Stub/SIM always True so harnesses never trip the no-game pause.
    v1413 — Windows: process-alive OR window pin (exclusive fullscreen often has no EnumWindows hit)."""
    if os.environ.get("TV_STUB") or os.environ.get("TV_NO_GAME_GUARD") == "0":
        return True
    if WATCH_MODE:
        # Windows: capture half owns pin; also honor D2R.exe process (v1413)
        try:
            tp = os.path.join(FRAMES, "cap_target.json")
            if os.path.isfile(tp):
                with open(tp, encoding="utf-8") as f:
                    j = json.load(f) or {}
                mode = str(j.get("mode") or "").lower()
                if mode in ("window", "game", "d2r"):
                    return True
                if j.get("d2rProcess") is True:
                    return True
                if mode in ("waiting", "none", "missing"):
                    # still open if process is alive (pin lag / exclusive FS)
                    if _win_d2r_process_alive():
                        return True
                    return False
        except Exception:
            pass
        if _win_d2r_process_alive():
            return True
        # eye fresh + large enough → assume capture half is alive (don't block Win falsely)
        try:
            eye = os.path.join(FRAMES, "eye.jpg")
            if os.path.isfile(eye) and (time.time() - os.path.getmtime(eye)) < 3.0:
                return True
        except Exception:
            pass
        return True  # fail-open on Windows unless explicitly waiting
    # Mac: only D2R.exe (never CrossOver Home / Battle.net)
    try:
        if find_d2r_window_mac() is not None:
            return True
    except Exception:
        pass
    # v927.5 — PROCESS-ALIVE FALLBACK: during loading screens / Space transitions macOS
    # drops the game-sized window from CGWindowList for minutes (live evidence 15:45:
    # 224s HOLD mid-session; D2R spawns 6 windows and only the 1470×956 one qualifies).
    # If the D2R.exe process is alive the game exists — keep the gate open and let the
    # full-screen capture lane carry the feed until the window re-lists.
    _pn = time.time()
    _pc = globals().get("_D2R_PROC_CACHE")
    if _pc and (_pn - _pc[1]) < 5.0:
        return _pc[0]
    alive = False
    try:
        out = subprocess.run(["pgrep", "-f", "D2R.exe"], capture_output=True, timeout=3)
        alive = out.returncode == 0
    except Exception:
        alive = False
    globals()["_D2R_PROC_CACHE"] = (alive, _pn)
    return alive


def _set_game_gate(ok, msg=""):
    """Publish no-game pause into health/state for the console banner."""
    globals()["_GAME_OK"] = bool(ok)
    globals()["_AI_PAUSED"] = not bool(ok)
    globals()["_GAME_MSG"] = (msg or "")[:160]
    try:
        with _state_lock:
            st = _load()
            st["gameOk"] = bool(ok)
            st["aiPaused"] = not bool(ok)
            st["gameMsg"] = globals()["_GAME_MSG"]
            if not ok:
                st["phase"] = "hold"
            _save(st)
    except Exception:
        pass
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
# v944 EVICTION JUSTICE — a hover streak floods the ring with text-eye freezes (one per new
# tooltip). The base cap must NEVER shed one text-eye freeze to make room for another; grant
# the priority (text-eye) class this many EXTRA slots before it may shed its own oldest.
PRIORITY_CAP_BONUS = max(0, int(os.environ.get("TV_PRIORITY_CAP_BONUS", "6") or 6))
SETTLE_QUEUE_STALE_MS = max(1000, int(os.environ.get("TV_SETTLE_QUEUE_STALE_MS", "120000") or 120000))
_SETTLE_QUEUE = []              # FIFO, newest last; each: {"path","sig","ts","interest","priority","origin"}
# v944 SECOND-EYE SWEEP — text-eye freezes superseded by the newest-wins live drain are NOT
# deleted (that was KAI's 'missed-text'); they wait here, files on disk, for the verify-gap
# sweeper to read them one at a time before seal. Bounded; stale-pruned; dies with the session.
_TEXT_EYE_BACKLOG = []
# v946 — slightly deeper backlog so hover-streak freezes survive longer for the sweeper
TEXT_EYE_BACKLOG_CAP = max(4, int(os.environ.get("TV_TEXT_EYE_BACKLOG_CAP", "32") or 32))
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

def _text_eye_backlog_add(entry):
    """v944 — hold an un-read text-eye freeze the newest-wins drain superseded, so the
    second-eye sweeper can still read it. Caller holds _settle_q_lock. Deduped by sig;
    bounded (oldest sheds only if the sweeper falls TEXT_EYE_BACKLOG_CAP behind)."""
    try:
        for b in _TEXT_EYE_BACKLOG:
            if sig_diff(entry.get("sig"), b.get("sig")) <= SETTLE:
                _settle_file_del(entry)   # already backlogged this exact view
                return
        _TEXT_EYE_BACKLOG.append(entry)
        while len(_TEXT_EYE_BACKLOG) > TEXT_EYE_BACKLOG_CAP:
            _settle_file_del(_TEXT_EYE_BACKLOG.pop(0))
    except Exception:
        _settle_file_del(entry)

def _text_eye_backlog_pop():
    """v944 — pop the OLDEST un-read text-eye freeze (earliest at-risk item first). Stale
    entries (>SETTLE_QUEUE_STALE_MS) are pruned. Returns the entry (file still on disk) or None."""
    now = int(time.time() * 1000)
    with _settle_q_lock:
        fresh, dropped = [], 0
        for e in _TEXT_EYE_BACKLOG:
            if now - e["ts"] > SETTLE_QUEUE_STALE_MS:
                _settle_file_del(e); dropped += 1
            else:
                fresh.append(e)
        _TEXT_EYE_BACKLOG[:] = fresh
        if dropped:
            ev("cap", "text-eye backlog — dropped %d stale freeze(s) (>%ds) unswept before seal"
               % (dropped, SETTLE_QUEUE_STALE_MS // 1000))
        if not _TEXT_EYE_BACKLOG:
            return None
        return _TEXT_EYE_BACKLOG.pop(0)

def _text_eye_backlog_len():
    """v948.17 (Grok P1-4) — peek the backlog size without popping (decision-only, no mutation)."""
    with _settle_q_lock:
        return len(_TEXT_EYE_BACKLOG)

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
            # v944 EVICTION JUSTICE (Konyo: "catch these BEFORE KAI") — the old `pop(0)` shed the
            # oldest freeze regardless of origin, so a hover streak ate its own earlier text-eye
            # freezes → KAI's 'missed-text'. Now: evict the oldest NON-priority (ambient settle)
            # view first; a text-eye freeze is shed only when the ring is ALL text-eye AND past
            # the raised cap (CAP + PRIORITY_CAP_BONUS). Files are tiny — disk is not the limit.
            while len(_SETTLE_QUEUE) > SETTLE_QUEUE_CAP:
                _victim = next((i for i, e in enumerate(_SETTLE_QUEUE) if not e.get("priority")), None)
                if _victim is not None:
                    _settle_file_del(_SETTLE_QUEUE.pop(_victim))
                    continue
                # all-priority ring: hold up to the raised cap before shedding the oldest text-eye
                if len(_SETTLE_QUEUE) > SETTLE_QUEUE_CAP + PRIORITY_CAP_BONUS:
                    _settle_file_del(_SETTLE_QUEUE.pop(0))
                else:
                    break
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
        entry = _SETTLE_QUEUE.pop()      # newest = most-current view (first eye reads this live)
        for e in _SETTLE_QUEUE:          # older held views are superseded for LIVE currency…
            if e.get("origin") == "text-eye" and e.get("path") and os.path.isfile(e.get("path")):
                _text_eye_backlog_add(e)   # …but an un-read item-text is NOT moot — sweep it later
            else:
                _settle_file_del(e)        # ambient settle views really are moot once newer exists
        _SETTLE_QUEUE[:] = []
        return entry

def _settle_queue_clear():
    """v825 — the queue dies with the session (farewell/shutdown), _eye_clear-style: drop every
    held file so a fresh ON never drains yesterday's freezes. Never raises."""
    with _settle_q_lock:
        for e in _SETTLE_QUEUE:
            _settle_file_del(e)
        _SETTLE_QUEUE[:] = []
        for e in _TEXT_EYE_BACKLOG:   # v944 — the sweep backlog dies with the session too
            _settle_file_del(e)
        _TEXT_EYE_BACKLOG[:] = []
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
    # v1463 — only take this branch when the seam yields a USABLE argv. v1461 returned
    # _argv_seam(...) unconditionally, so a malformed value (TV_OCR_ARGV=1, [], {}, "claude")
    # fell back to [OCR_BIN, "--worker"] and jumped the queue: on Windows that skipped the
    # ocr_win.ps1 branch below and tried to exec the checked-in Mach-O `bin/ocr_mac`, and on
    # Mac it skipped the isfile/X_OK guard. A bad env var must never beat the platform lane.
    _ocr_argv = _argv_seam("TV_OCR_ARGV", []) if os.environ.get("TV_OCR_ARGV") else []
    if _ocr_argv:
        return _ocr_argv
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
# v925 LIGHT — OCR lane OFF by default (Grok cut #4): the "1 claude" product doesn't need the
# extra grab+process per candidate. TV_OCR=1 (or heavy/robot) re-arms it.
# v941 — LANES ON BY DEFAULT, PERIOD. The v925-LIGHT off-defaults bit FOUR times (OCR
# twice, FILM twice) — every new launch path that skipped the launcher's exports silently
# killed the fast lane + text eye + footage. Disable explicitly (TV_OCR=0) or not at all.
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
                # v1200 — same class as VisionWorker.ask(): monotonic, not wall-clock, so a
                # backward NTP jump mid-poll can't balloon the wait past the intended budget
                # (short window here, 1.2-1.5s, but the OCR/text-eye lane depends on it staying
                # fast every single poll — a stuck wait here starves the whole fast lane).
                deadline = time.monotonic() + timeout
                while time.monotonic() < deadline:
                    try:
                        line = self.q.get(timeout=max(0.05, deadline - time.monotonic()))
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
                        # v1709 — mode=err with lines=[] is a FAILED read, not loot.
                        # Returning it let ocr_fast stamp scene=loot / conf=0.45 / mode=ocr.
                        if str(j.get("mode") or "") == "err":
                            return None
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
    # v935.7 — console chrome (text-eye burned a Sonnet read on STANDBY/LIVE at boot)
    "standby", "on air", "off air", "watching", "signal idle", "press on",
    "live eye", "second eye", "three eyes", "auto intake", "tv diablo",
    "simulation", "farm day", "last thought",
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

def _text_eye_loop():
    """v932 — 👁‍🗨 THE TEXT-TRIGGERED EYE (Konyo forensic case: '20 items shown, 4 reads').
    The motion-settle detector is blind to tooltips and tab swaps — small pixel deltas on a
    static stash view never trip a read. This lane OCR-scans the live eye continuously
    (local Vision, ~50-150ms) and turns NEW item-ish text into an immediate PRIORITY read
    of the frozen frame via _settle_enqueue (whose drain path bypasses the same-view gate,
    so these can never be deduped away). Text re-arms after a TTL so revisits re-read."""
    if os.environ.get("TV_TEXT_EYE", "1") == "0" or not _OCR.available():
        return
    eye = os.path.join(FRAMES, "eye.jpg")
    seen = {}          # normalized text → last-seen monotonic ts
    TTL = 150.0
    last_area = None
    while True:
        try:
            time.sleep(0.7)
            # v937.1 — NEW AREA = fresh eyes: the same item names in a new run must
            # re-trigger (a second Shako in the next Baal run is a new event, not a dup).
            _ar = globals().get("LAST_AREA")
            if _ar != last_area:
                last_area = _ar
                if seen:
                    seen.clear()
            if globals().get("_AI_PAUSED") or not os.path.isfile(eye):
                continue
            # v934.2 / v935.7 — NO PIN, NO SCAN. Boot default used to be mode="full", so the
            # text eye OCR'd console chrome (STANDBY / LIVE) and burned a Sonnet read.
            # Only a real D2R *window* pin is allowed — never full-screen / waiting / none.
            _cap = _CAP_TARGET or {}
            if not WATCH_MODE and (_cap.get("mode") != "window" or not _cap.get("wid")):
                continue
            if (time.time() - os.path.getmtime(eye)) > 3.0:
                continue   # film cold — nothing fresh under the eye
            raw = _OCR.read(eye, timeout=1.5)
            if not raw:
                continue
            names = filter_ocr_lines(raw.get("lines") or [])
            now = time.monotonic()
            for k in [k for k, t in seen.items() if now - t > TTL]:
                del seen[k]
            fresh = []
            for nm in names:
                key = _norm_name(nm)
                if not key:
                    continue
                # v1379 — OCR garble ("haTrng1.. Lobby", "'Ii'", "ING THe R") was enqueuing
                # priority Sonnet reads every ~0.7s. Gate on _text_eye_worthy (stricter than
                # _itemish) so only real-looking item labels burn a subscription vision turn.
                if not _text_eye_worthy(nm):
                    seen[key] = now   # still mark seen so garble doesn't re-arm forever
                    continue
                if key not in seen:
                    fresh.append(nm)
                seen[key] = now
            if not fresh:
                continue
            # v1379 — cooldown: after a text-eye fire, wait before another (cap spam)
            last_fire = globals().get("_TEXT_EYE_LAST_FIRE") or 0.0
            try:
                min_gap = float(os.environ.get("TV_TEXT_EYE_MIN_GAP_S", "4") or 4)
            except Exception:
                min_gap = 4.0
            if now - last_fire < min_gap:
                continue
            try:
                sig = frame_sig(eye)
            except Exception:
                continue
            globals()["_TEXT_EYE_LAST_FIRE"] = now
            _settle_enqueue(eye, sig, interest=0.95, priority=True, origin="text-eye")
            ev("settle", "👁‍🗨 text eye — new text: " + ", ".join(fresh[:3])
               + (" …" if len(fresh) > 3 else "") + " → priority read of the frozen frame")
            # v937 — the trigger is EVIDENCE: journal it so SIM shows WHY a priority read
            # fired at this instant, and the Watchdog can assert text-eye liveness.
            try:
                journal_skip("text-eye", "👁‍🗨 triggered by: " + ", ".join(fresh[:4]))
            except Exception:
                pass
        except Exception:
            time.sleep(2.0)


def ocr_fast(path):
    """Fast lane: local OCR → provisional names. Target warm p50 < 50ms, p99 < 200ms."""
    if not OCR_ENABLED or os.environ.get("TV_OCR") == "0":
        return None
    t0 = time.time()
    raw = _OCR.read(path)
    wall = int((time.time() - t0) * 1000)
    if not raw or str(raw.get("mode") or "") == "err":
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
    ever stalling the other 7. Defaults to worker 0 for old callers.

    v1192 — that "other 7" is the whole premise: this only helps when OTHER pool slots are
    free to keep serving live traffic while this one warms in the background. Outside
    ROBOT_MODE, POOL_N==1 ("ONE Claude always" — Konyo's actual live config) means there IS
    no other slot; `w` here is the SAME VisionWorker every live read uses, and `w.ask()`
    below holds `w.lock` for up to 60s — a `Reply with exactly: ok` ping that a live read
    arriving moments later would silently queue behind, waiting on the lock BEFORE its own
    LIVE_READ_TIMEOUT_S budget even starts counting. That defeats the Master Brain law
    (v948.17) worse than the outage it's meant to route around: a dead worker already
    self-heals for free (`ask()`'s own `self.p.poll() is not None` respawn, first thing on the
    very next call), so a POOL_N==1 background ping only adds contention with no upside. Skip
    it there; keep it for the real multi-reader pool it was written for."""
    if POOL_N <= 1:
        return
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


# v1818 — the panel's sort order, and the shape a First Found stamp must have.
#
# _CHRON_STAMP_RX is not decoration. The UNIQUE and SETS tabs print `First Found:` and
# `Dropped By:` in OPPOSITE orders (verified on his 08-20 frames), so the single most likely
# reader error is filling foundAt with a monster name. A stamp that is not a date is DROPPED and
# audited rather than stored: a wrong find-date would outlive every later correction, because
# nothing downstream re-reads a date it already has.
# Compiled on first use, not at import: this module has NO module-level `re` (its convention is a
# local `import re as _re` inside the functions that need it), and a top-level re.compile here
# raised NameError at import — caught by running the parser rather than by reading it.
_CHRON_STAMP_RX = None


def _chron_stamp_ok(v):
    """True when v looks like the game's own `First Found` stamp, e.g. 08/20/2026, 00:49."""
    global _CHRON_STAMP_RX
    if _CHRON_STAMP_RX is None:
        import re as _re
        _CHRON_STAMP_RX = _re.compile(r"^\s*\d{1,2}/\d{1,2}/\d{4}\s*,?\s*\d{1,2}:\d{2}(:\d{2})?\s*$")
    return bool(_CHRON_STAMP_RX.match(v or ""))


def _norm_chron_sort(raw, scene=None):
    """newest | oldest | other | "" — and "" whenever the scene is not a chronicle page."""
    if scene is not None and scene != "chronicle":
        return ""
    v = str(raw or "").strip().lower()
    if not v:
        return ""
    if "newest" in v and "oldest" in v:
        return "newest" if v.index("newest") < v.index("oldest") else "oldest"
    if v in ("newest", "oldest", "other"):
        return v
    if "newest" in v:
        return "newest"
    if "oldest" in v:
        return "oldest"
    return "other"


def _norm_chron_tab(raw, scene=None):
    """v1512 — WHICH CHRONICLE LEDGER is on screen: "uniques" | "sets" | "".

    Only meaningful when scene=chronicle, and deliberately STRICT: anything the reader was not sure
    about comes back "" rather than a guess. The two ledgers are two different stores (d2r_foundLog
    vs d2r_setPieces) — an unknown ledger just costs a re-read, a WRONG one writes set pieces into
    his grail. So the fuzzy matching that serves the stash tabs well would be the wrong instinct here.
    """
    if scene is not None and scene != "chronicle":
        return ""
    lo = str(raw or "").strip().lower()
    if lo in ("uniques", "unique", "holy grail", "grail"):
        return "uniques"
    if lo in ("sets", "set", "set pieces", "setpieces"):
        return "sets"
    return ""


# v946.1 — STASH TAB IDENTITY (live farm: gems/materials never journaled when model said only
# "shared"/empty). Tab-strip OCR + sticky walk so tally tabs stick for driver/KAI time-map.
_STASH_TAB_STICKY = {"open": False, "tab": "", "ts": 0}
_TALLY_STASH_TABS = frozenset(("runes", "gems", "materials"))


def _tab_from_ocr_lines(lines):
    """Pure: active RotW tab from OCR. Multi-tab chrome → '' (stash_eye / v947)."""
    try:
        from stash_eye import tab_from_ocr_lines as _se_tab
        return _se_tab(lines)
    except Exception:
        import re as _re
        blob = " ".join(str(t).lower() for t in (lines or []))
        if not blob.strip():
            return ""
        order = (
            ("materials", "materials"), ("material", "materials"),
            ("runes", "runes"), ("gems", "gems"),
            ("personal", "personal"), ("shared", "shared"),
            ("rune", "runes"), ("gem", "gems"), ("mat", "materials"),
        )
        hits = []
        for key, canon in order:
            if _re.search(r"(?<![a-z])" + _re.escape(key) + r"(?![a-z])", blob):
                if canon not in hits:
                    hits.append(canon)
        return hits[0] if len(hits) == 1 else ""


def _crop_left_tab_strip(src_path, dest_path, frac=0.20):
    """Legacy left-20% crop (fallback). Prefer stash_eye.prep_tab_chrome for v947 eyes."""
    try:
        from PIL import Image  # type: ignore
        im = Image.open(src_path)
        w, h = im.size
        if w < 32 or h < 32:
            return None
        box = (0, 0, max(8, int(w * frac)), h)
        im.crop(box).convert("RGB").save(dest_path, format="JPEG", quality=90)
        return dest_path
    except Exception:
        return None


def _stash_tab_ocr_path(frame_path, model_tab=""):
    """v947 — intake-style tab chrome + grid fingerprint (no intake calls).

    Mimics bible `_tallyPrepImage` crop band: upscaled tab chrome above left grid,
    then pixel grid class (runes/gems/materials). Used by live deep journal stashTab.

    v948.20 — model_tab corroboration: the caller (_resolve_stash_tab) only reaches
    here having ALREADY confirmed scene=='stash' from the model read, i.e. the stash
    panel IS open. Passing that through as model_tab lets the grid fingerprint's
    confident tally read (esp. the moderate-chroma GEMS grid) satisfy fuse_tab_signals'
    stash-open corroboration instead of being dropped for lack of a live journal sticky
    — WITHOUT relaxing the live loading-screen guard (which keys off the panel being
    open, which we know it is). Chrome OCR can't disambiguate the active tab (it prints
    ALL five labels → ambiguous → ''), so the grid is the real gems signal.
    """
    if not frame_path or not os.path.isfile(frame_path):
        return ""
    try:
        from stash_eye import analyze_frame

        def _read(p):
            if not _OCR.available():
                return {}
            try:
                return _OCR.read(p, timeout=1.5) or {}
            except Exception:
                return {}

        res = analyze_frame(
            frame_path,
            ocr_lines=None,
            journal_tab="",
            model_tab=(model_tab or "stash"),
            ocr_worker_read=_read if _OCR.available() else None,
            work_dir=HIST_DIR,
        )
        tab = str(res.get("tab") or "")
        if tab in ("runes", "gems", "materials", "personal", "shared"):
            return tab
        # fallback: legacy left strip if eyes returned empty
        if not _OCR.available():
            return ""
        crop = os.path.join(HIST_DIR, ".tabstrip_ocr.jpg")
        os.makedirs(HIST_DIR, exist_ok=True)
        use = _crop_left_tab_strip(frame_path, crop) or frame_path
        j = _OCR.read(use, timeout=1.5)
        return _tab_from_ocr_lines((j or {}).get("lines") or [])
    except Exception:
        return ""


# ══ v1522 — THE LIVE CHRONICLE VISIT ══════════════════════════════════════════════════════════
# Konyo: "when chronicle/menu is clicked ingame it should automatically know we are about to register
# and read and analyze the CHRONICLE lists."
#
# WHAT IT DOES AND DELIBERATELY DOES NOT DO. It RECORDS the visit — every frame, which ledger, how
# long — and that costs nothing. It does NOT fire chronicle reads mid-farm: that would spend his
# subscription reads without asking, in the middle of a run, on frames he is scrolling past. The
# recorded visit becomes an offer ("📜 a Chronicle visit was captured — 14 frames, Holy Grail ledger"),
# and the read is the same priced, reviewable, gated sweep the retro lane already uses. Same doctrine
# everywhere: see the price, then decide.
#
# THE STICKY exists because the ledger is read off the panel's tab header, and mid-scroll frames often
# do not show it. Losing the ledger halfway through a visit would split one visit into an identified
# half and an unidentified half — so the first confident answer holds for the whole visit, and a
# CONTRADICTING answer ends it (he switched tabs; that is genuinely a new visit).
_CHRON_VISIT = {"open": False, "ledger": "", "since": 0, "last": 0, "frames": []}
_CHRON_VISIT_MAX = 400   # a visit is minutes of frames, not a session; the cap is a memory guard


def _chron_visit_step(scene, chron_tab, frame_id=None, ts=None):
    """Advance the live visit state machine. Returns a CLOSED visit dict when one just ended, else None.

    Closing on the way OUT (rather than reporting continuously) is what makes the visit a single
    reviewable thing with a real frame count — a half-open visit has no honest number to show."""
    ts = int(ts or time.time() * 1000)
    scene = str(scene or "").lower()
    tab = _norm_chron_tab(chron_tab, "chronicle" if scene == "chronicle" else None)

    def _close():
        if not _CHRON_VISIT["open"]:
            return None
        out = {"ledger": _CHRON_VISIT["ledger"], "since": _CHRON_VISIT["since"],
               "until": _CHRON_VISIT["last"], "frames": list(_CHRON_VISIT["frames"])}
        out["n"] = len(out["frames"])
        _CHRON_VISIT.update({"open": False, "ledger": "", "since": 0, "last": 0, "frames": []})
        return out

    if scene != "chronicle":
        return _close()
    # a CONTRADICTING ledger means he switched tabs — that is a new visit, not a confused one
    if _CHRON_VISIT["open"] and tab and _CHRON_VISIT["ledger"] and tab != _CHRON_VISIT["ledger"]:
        closed = _close()
        _CHRON_VISIT.update({"open": True, "ledger": tab, "since": ts, "last": ts,
                             "frames": [frame_id] if frame_id else []})
        return closed
    if not _CHRON_VISIT["open"]:
        _CHRON_VISIT.update({"open": True, "ledger": tab, "since": ts, "last": ts, "frames": []})
    if tab and not _CHRON_VISIT["ledger"]:
        _CHRON_VISIT["ledger"] = tab          # the sticky: first confident answer holds the visit
    _CHRON_VISIT["last"] = ts
    if frame_id and len(_CHRON_VISIT["frames"]) < _CHRON_VISIT_MAX:
        _CHRON_VISIT["frames"].append(frame_id)
    return None


def chron_visit_open():
    """Is a Chronicle panel open RIGHT NOW — the 'we are about to register' signal, for the console."""
    return {"open": bool(_CHRON_VISIT["open"]), "ledger": _CHRON_VISIT["ledger"],
            "since": _CHRON_VISIT["since"], "frames": len(_CHRON_VISIT["frames"])}


def chron_visit_flush():
    """v1689 — SEAL A STILL-OPEN CHRONICLE VISIT AT SESSION CLOSE, so it reaches the journal.

    The state machine above only closes a visit on the way OUT — i.e. when a LATER deep read
    returns a non-chronicle scene. That lost the most natural way to use the feature: looking at
    the Chronicle LAST and then stopping. Measured on his session s_1786385768689_67392
    (2026-08-10 21:16-21:19): 8 deep frames scene='chronicle' / chronicleTab='uniques', the visit
    still {open:True, frames:8} at the end, and ZERO {lane:'chronicle', kind:'visit'} rows written
    — so /api/chronicle_visits (which filters on exactly that row) stayed [] and the v1527 "read
    this visit for ZERO classifies" offer could never appear.

    Session close is the honest seam: the reel stops growing there, so the frame count is final.
    Doctrine is unchanged — recording is FREE, reading is OFFERED. This journals the visit and says
    so; it never calls claude_chronicle_read / g5_chronicle_read and never spends a classify.
    Idempotent: closing leaves the visit shut, so a second call journals nothing.

    Returns the closed visit dict when one was journalled, else None.
    (The ev/_journal pair below is deliberately NOT shared with the live seam at the deep-read
    call site: test_agent.py slices that seam's SOURCE TEXT to prove the live lane never fires a
    read, and folding it into a helper would erase the text it reads.)"""
    try:
        _closed_visit = _chron_visit_step(None, None)
    except Exception:
        return None
    if not (_closed_visit and _closed_visit.get("n")):
        return None
    _lg = _closed_visit.get("ledger") or ""
    try:
        ev("read", "📜 Chronicle visit captured — %d frames%s · ask the console to read it"
           % (_closed_visit["n"], (" · " + ("Holy Grail" if _lg == "uniques" else "Set pieces"))
              if _lg else " · ledger unread"))
        _journal({"lane": "chronicle", "kind": "visit", "ts": int(time.time() * 1000),
                 "ledger": _lg, "frames": _closed_visit["frames"][:120],
                 "n": _closed_visit["n"], "since": _closed_visit["since"],
                 "until": _closed_visit["until"]})
    except Exception:
        pass
    return _closed_visit


def _resolve_stash_tab(scene, model_tab, frame_path=None, ocr_rd=None, ts=None):
    """v946.1 — final stashTab for journal/driver: model + tab-strip OCR + sticky walk.

    Rules:
      · leave stash → clear sticky
      · tally-tab words from OCR beat a vague model 'shared'/'personal'/empty (farm proof)
      · while still on stash with no new signal, hold last sticky tab (tab walk)
    """
    ts = int(ts or time.time() * 1000)
    scene = str(scene or "")
    if scene != "stash":
        if scene in ("town", "loot", "gameplay", "transition"):
            _STASH_TAB_STICKY["open"] = False
            _STASH_TAB_STICKY["tab"] = ""
            _STASH_TAB_STICKY["ts"] = 0
        return ""

    model = _norm_stash_tab(model_tab, "stash")
    ocr_tab = ""
    try:
        lines = []
        if isinstance(ocr_rd, dict):
            lines = list(ocr_rd.get("raw_lines") or ocr_rd.get("lines") or [])
        if lines:
            ocr_tab = _tab_from_ocr_lines(lines)
        if not ocr_tab and frame_path:
            # v948.20 — pass the model tab (or bare 'stash', panel is open) so a
            # confident grid gems/materials/runes read isn't dropped for want of a sticky.
            ocr_tab = _stash_tab_ocr_path(frame_path, model_tab=model)
    except Exception:
        ocr_tab = ""

    tab = model
    # OCR tally tabs win over model vault/empty (console "saw gems" but journal said shared)
    if ocr_tab in _TALLY_STASH_TABS and model not in _TALLY_STASH_TABS:
        tab = ocr_tab
    elif ocr_tab and not model:
        tab = ocr_tab
    elif ocr_tab and model and ocr_tab != model and ocr_tab in _TALLY_STASH_TABS:
        tab = ocr_tab
    elif not tab and ocr_tab:
        tab = ocr_tab

    # sticky walk: hold last tab while still on stash if nothing new
    if not tab and _STASH_TAB_STICKY.get("open") and _STASH_TAB_STICKY.get("tab"):
        if ts - int(_STASH_TAB_STICKY.get("ts") or 0) <= 25_000:
            tab = _STASH_TAB_STICKY["tab"]

    if tab:
        _STASH_TAB_STICKY["open"] = True
        _STASH_TAB_STICKY["tab"] = tab
        _STASH_TAB_STICKY["ts"] = ts
    else:
        _STASH_TAB_STICKY["open"] = True  # in stash, tab still unknown
    return tab


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
    if scene not in ("town", "loot", "inventory", "stash", "gameplay", "transition", "chronicle"):
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
    chron_tab = _norm_chron_tab(j.get("chronicleTab") or j.get("chronicle_tab"), scene)
    discovered = [str(x).strip() for x in (j.get("discovered") or []) if str(x).strip()][:12]
    # v1818 — the chronicle's own dates, kept only when they are actually dates
    chron_sort = _norm_chron_sort(j.get("chronicleSort") or j.get("chronicle_sort"), scene)
    found_at, dropped_by = {}, {}
    try:
        _fa = j.get("foundAt") or j.get("found_at") or {}
        if isinstance(_fa, dict):
            for k3, v3 in list(_fa.items())[:80]:
                k3 = str(k3).strip()[:64]
                v3 = str(v3).strip()[:32]
                if not k3 or not v3:
                    continue
                if _chron_stamp_ok(v3):
                    found_at[k3] = v3
                else:
                    _audit["dropped"].append({"field": "foundAt", "from": v3[:24],
                                              "why": "not-a-timestamp"})
        _db = j.get("droppedBy") or j.get("dropped_by") or {}
        if isinstance(_db, dict):
            for k4, v4 in list(_db.items())[:80]:
                k4 = str(k4).strip()[:64]
                v4 = str(v4).strip()[:48]
                if k4 and v4 and not _chron_stamp_ok(v4):
                    dropped_by[k4] = v4
                elif k4 and v4:
                    _audit["dropped"].append({"field": "droppedBy", "from": v4[:24],
                                              "why": "looks-like-a-timestamp"})
    except Exception:
        found_at, dropped_by = {}, {}
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
    # v946.5 (Konyo: "was the Diadem read 3 socketed?") — capture the socket count per item.
    # name -> N (1..6). Read from the tooltip's 'Socketed (N)' line, never guessed from base type.
    sockets = {}
    try:
        raw_sk = j.get("sockets") or {}
        if isinstance(raw_sk, dict):
            for k3, v3 in list(raw_sk.items())[:60]:
                try:
                    n3 = int(v3)
                except Exception:
                    _audit["dropped"].append({"field": "sockets." + str(k3)[:30], "from": str(v3)[:12], "why": "not-an-int"})
                    continue
                if 1 <= n3 <= 6:   # every D2R socketable item holds 1..6
                    sockets[str(k3).strip()] = n3
                else:
                    _audit["dropped"].append({"field": "sockets." + str(k3)[:30], "from": str(n3), "why": "out-of-range-1-6"})
    except Exception:
        sockets = {}
    return {"area": str(j.get("area", "")).strip()[:48], "scene": scene, "names": names,
            "tz": tz, "conf": conf, "stashTab": stash_tab,
            "chronicleTab": chron_tab,   # v1512 — WHICH ledger; "" when unsure, never a guess
            "discovered": discovered,
            "names_loc": names_loc,
            "sockets": sockets,
            "chronicleSort": chron_sort,   # v1818 — newest|oldest|other|""
            "foundAt": found_at,           # v1818 — name -> the row's own First Found stamp
            "droppedBy": dropped_by,       # v1818 — name -> the monster on its Dropped By line
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
# Bare / vision-fluff labels.
# v1576 HONESTY — this comment used to read "must never auto-vault without a real identity
# chain", which described a guard that NOTHING ENFORCES. Its only consumer is _is_weak_name()
# below, and _is_weak_name() has ZERO callers in the repo (grep: tv/, bible.html — one hit, its
# own def). Executed proof: LootLifecycle._on_loot(["Ring","Jewel"], ...) tags both "seen" (not
# "skip-weak") and the resulting chain carries them straight into _on_stash → _commit. The rule
# that IS live is the v738 universal chain gate in _on_stash (SEEN/HOLDING/candidate required
# for EVERY name) — which happens to be exactly what _is_weak_name's docstring asked for, so
# behaviour is unchanged; only the claim was false. Whether these bare labels should ALSO be
# barred from BUILDING that provenance in _on_loot is a product call — PARKED for Konyo, since
# a real D2R jewel's floor label literally is "Jewel" and gating it would lose true drops.
# Kept (not deleted) because the curated list is the input any future gate would use.
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


# ── v948 SESSION STICKY (Konyo: shared/stash always-there items re-read every deep) ──
# Learns which names are stable this session (cube/tomes on inventory, worn gear, stash
# rows already hovered). Re-reports as ECHO (not NEW) until they MOVE or leave.
# New items + location changes stay first-class. Cleared on new SESSION_ID.
_SESSION_STICKY = {}   # norm_name -> {name, loc, tab, firstTs, lastTs, count}
_SESSION_STICKY_SID = ""


def _sticky_reset_if_new_session():
    global _SESSION_STICKY, _SESSION_STICKY_SID
    sid = SESSION_ID or ""
    if sid != _SESSION_STICKY_SID:
        _SESSION_STICKY = {}
        _SESSION_STICKY_SID = sid


def _classify_name_sticky(names, names_loc, stash_tab, scene, now_ms):
    """Split names into new / echo / moved for this session.
    Policy (brains 1–5 filter):
      1. first sighting of a name → NEW
      2. same name, different loc or stash tab → MOVED (re-report)
      3. anchors + equipped after first → ECHO (always-on UI)
      4. inventory non-anchor after first → ECHO (charms already held)
      5. stash same tab after first → ECHO (shared grid re-hover)
      floor / loot always prefers NEW if area changed (handled by text-eye clear);
      floor re-sight same area without gap → ECHO after first.
    Returns (names_new, names_echo, names_moved, tags_extra).
    """
    _sticky_reset_if_new_session()
    names = list(names or [])
    names_loc = names_loc or {}
    tab = str(stash_tab or "").lower()
    scene = str(scene or "")
    new, echo, moved = [], [], []
    tags = {}
    for n in names:
        k = _norm_name(n)
        if not k:
            continue
        loc = str(names_loc.get(n) or "").lower()
        # default loc by scene when model omitted names_loc
        if not loc:
            if scene == "stash":
                loc = "stash"
            elif scene == "inventory":
                loc = "inventory"
            elif scene == "loot":
                loc = "floor"
        prev = _SESSION_STICKY.get(k)
        if not prev:
            _SESSION_STICKY[k] = {
                "name": n, "loc": loc, "tab": tab if loc == "stash" else "",
                "firstTs": now_ms, "lastTs": now_ms, "count": 1,
            }
            new.append(n)
            tags[n] = "first-seen"
            continue
        prev["lastTs"] = now_ms
        prev["count"] = int(prev.get("count") or 0) + 1
        prev_loc = str(prev.get("loc") or "")
        prev_tab = str(prev.get("tab") or "")
        loc_changed = prev_loc and loc and prev_loc != loc
        tab_changed = (loc == "stash" and prev_tab and tab and prev_tab != tab)
        if loc_changed or tab_changed:
            prev["loc"] = loc
            if loc == "stash":
                prev["tab"] = tab
            moved.append(n)
            new.append(n)  # still "newsworthy"
            tags[n] = "moved:" + (prev_loc or "?") + "→" + (loc or "?")
            continue
        # stable position — sticky echo for always-on UI pieces
        if _is_anchor(n) or loc == "equipped":
            echo.append(n)
            tags[n] = "echo-sticky"
            continue
        if loc == "inventory":
            echo.append(n)
            tags[n] = "echo-sticky"
            continue
        if loc == "stash" and tab:
            # same tab re-hover of same name (shared grid always shows many items)
            echo.append(n)
            tags[n] = "echo-sticky"
            continue
        if loc == "floor":
            # re-seen on floor without area clear — still echo after first
            echo.append(n)
            tags[n] = "echo-sticky"
            continue
        # unknown loc: treat as echo after first to kill spam
        echo.append(n)
        tags[n] = "echo-sticky"
    return new, echo, moved, tags

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
    """UNREACHABLE as of v1576 — kept as the reference predicate for _WEAK_EXACT, NOT a live gate.

    Original claim: "Too generic alone — only stash-commits if already SEEN/HOLDING/candidate."
    That rule is real and IS enforced — but by the v738 chain gate in _on_stash, for every name,
    not by this function. This function has no caller (see the _WEAK_EXACT block above for the
    grep + executed evidence). Do not read a call to it into the pipeline; there isn't one.
    If you wire it up, that is a behaviour change: it would also reject bare-but-genuine floor
    labels ("Jewel"), which is the parked product question, not a bug fix."""
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
    """UNREACHABLE as of v1576 — zero callers repo-wide (grep tv/ bible.html: one hit, this def).
    No town-specific branch exists anywhere in the engine; nothing suppresses reads or loot
    provenance in town today. Kept as the town-name table any such gate would need. Whether the
    engine SHOULD gate on town is a product call — PARKED, not guessed at here."""
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

_SLOT_DEATHS = deque(maxlen=8)   # v891 (Grok C1) — timestamps of worker deaths
_THROTTLED_UNTIL = [0.0]
def _note_slot_death():
    """v891 — 2+ worker deaths inside 60s = subscription throttle cascade: soft-degrade for
    120s (heartbeat sheds to 1 via the cap, gap breathes) and SAY SO instead of silent empties."""
    now = time.time()
    _SLOT_DEATHS.append(now)
    recent = [t for t in _SLOT_DEATHS if now - t <= 60.0]
    if len(recent) >= 2 and now >= _THROTTLED_UNTIL[0]:
        _THROTTLED_UNTIL[0] = now + 120.0
        ev("cap", "🐢 THROTTLED — 2+ reader deaths in 60s (subscription pace?) · soft-degrade 120s, reads breathe")
        print("  🐢 throttle cascade detected — degrading softly for 120s")


def _is_throttled():
    return time.time() < _THROTTLED_UNTIL[0]


_ONESHOT_GATE = threading.Semaphore(1)   # v864 — a throttled pool must not herd 8 oneshots
_ASK_NONE_STREAK = 0
def _oneshot(ap, model, timeout=90, prompt=None, raw_json=False):
    """v864 — serialized: under subscription throttle all 8 workers can time out together;
    eight parallel one-shot bridges would herd the same throttle. One at a time.

    v1196 — the gate wait and the subprocess call each got the FULL `timeout` independently:
    a caller queued behind another one-shot (exactly the throttle-cascade this gate exists
    for — the scenario where several readers ALL fall to the bridge at once) could wait up to
    `timeout` just to acquire the gate, then get a fresh `timeout` for the run itself — up to
    2×timeout wall-clock for one call. Every caller passes LIVE_READ_TIMEOUT_S here specifically
    so a single live read can't exceed that budget (the Master Brain law); silently doubling it
    under the exact contention this gate was built to serialize defeated that. Spend the two
    phases OUT OF the same budget instead: whatever the wait cost, the run gets what's left.

    v1200 — `t0`/elapsed here is monotonic, not wall-clock: a backward NTP jump during the
    gate wait would otherwise make the wall-clock elapsed calculation go negative, INFLATING
    `remaining` well past the caller's intended budget — the same clock-skew class as
    VisionWorker.ask(), just bending the number the other way (too much budget instead of
    too little)."""
    t0 = time.monotonic()
    if not _ONESHOT_GATE.acquire(timeout=timeout):
        return None
    try:
        remaining = max(1.0, float(timeout) - (time.monotonic() - t0))
        return _oneshot_inner(ap, model, remaining, prompt=prompt, raw_json=raw_json)
    finally:
        _ONESHOT_GATE.release()


def _oneshot_inner(ap, model, timeout=90, prompt=None, raw_json=False):
    """v1519 — `prompt` / `raw_json` are the CHRONICLE seam, and both default to the old behaviour so
    every existing caller is byte-identical. The chronicle read asks a different question (found-state
    per row, not item names) and its answer must NOT go through _parse_read, which would shape it into
    the item contract and throw the found/notFound split away."""
    """One cold `claude -p` on subscription (strict-mcp, no API key).

    v1379 — circuit-breaker + lean CLI (no monorepo project load / no session persist)."""
    blocked = _sub_budget_check("oneshot")
    if blocked:
        ev("cap", blocked)
        journal_skip("sub-budget", blocked)
        return None
    env, stripped = _claude_env()
    _log_auth_once(stripped)
    add = [FRAMES]
    ap_dir = os.path.dirname(os.path.abspath(ap)) if ap else ""
    if ap_dir and os.path.isdir(ap_dir):
        add.append(ap_dir)
    args = _claude_lean_args(model, stream=False, add_dirs=add)
    # v1463 — insert the prompt after the "-p" FLAG, located by index. The old
    # `args[:2] + [PROMPT] + args[2:]` hard-coded "the binary is exactly argv[0]", which
    # v1461's TV_CLAUDE_ARGV seam broke: a multi-element prefix like
    # [python, -u, fake_claude.py] put the prompt at index 2 and produced
    # [python, -u, <PROMPT>, fake_claude.py, -p, ...] — the interpreter then treated the
    # prompt as the script name and every one-shot read exited 2. Production (seam unset)
    # was unaffected because the prefix is 1 long, which is exactly why no test caught it.
    try:
        _p_at = args.index("-p")
    except ValueError:
        _p_at = 0
    args = args[:_p_at + 1] + [prompt if prompt else READ_PROMPT.format(path=ap)] + args[_p_at + 1:]
    r = subprocess.run(
        args,
        capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL, env=env,
        cwd=_VISION_CWD,
        preexec_fn=(None if sys.platform == "win32" else (lambda: os.nice(10))))   # v876
    out = (r.stdout or "").strip()
    a, b = out.find("{"), out.rfind("}")
    if a < 0 or b <= a:
        err = (r.stderr or "").strip()[:160]
        ev("cap", f"vision returned no JSON ({model} exit {r.returncode})" + (f": {err}" if err else ""))
        journal_skip("parse-null", f"{model} exit {r.returncode}")   # v880 A2.8
        if r.returncode != 0:
            print(f"  ⚠ claude exit {r.returncode}" + (f": {err}" if err else ""))
        return None
    _sub_budget_record()
    globals()["_LAST_RAW"] = str(out)[:2048]   # v832 — THE THOUGHT (one-shot lane)
    if raw_json:
        try:
            return json.loads(out[a:b + 1])
        except Exception:
            journal_skip("parse-null", "%s raw-json unparseable" % model)
            return None
    _pr = _parse_read(out)
    if _pr is not None:
        _pr["_raw_txt"] = str(out)[:2048]
    return _pr

# v1519 — THE CHRONICLE LANE, Claude side. Konyo's PRIMARY reader: if this lane does not answer,
# there is no page (two_lane_read never pays Grok to second-guess a refusal).
#
# It is deliberately NOT READ_PROMPT with an extra field. READ_PROMPT asks "what items are on screen";
# this asks "which rows are marked FOUND", which is a different question with a different failure
# mode, and folding it into the live prompt would make every farming read carry chronicle instructions
# it can never use.
# ── v1785 — THE VAULT READER SEAM, WHICH HAD NEVER BEEN BUILT ────────────────────────────────────
# vault_retro.sweep() reads resp["items"] and the vault sweep was wired to claude_chronicle_read,
# whose answer has keys found/notFound/sets and no `items` at all. `note` is None on a GOOD chronicle
# read, so it was not even treated as a refusal: the page counted as read, the reel was marked swept,
# and no row could ever be produced. `grep -rn "def claude_vault"` returned nothing — the seam was
# missing, not broken. Found by an adversarial review of this lane.
#
# The contract is vault_retro's, not this file's: normalize_item() takes {name, lane, kind, count,
# conf, throwOut, throwWhy} and REFUSES a row with no name, so an invented row is impossible by
# construction. lane ∈ (stash, inventory, equipment); kind ∈ (rune, gem, material, item); both fall
# back to the surface's own default when the reader does not say, and never invent an item.
VAULT_READ_PROMPT = (
    "Image {path} = a Diablo II Resurrected (RotW mod) {surface} panel: a grid of item icons, some "
    "with a name label or a stack count.\n"
    "Reply with STRICT JSON only, no markdown, no prose:\n"
    '{{"surface":"{surface}","items":[],"conf":0.0}}\n'
    'Each item = {{"name":"<exact text you can read>","kind":"rune|gem|material|item",'
    '"count":<int or null>,"throwOut":false}}\n'
    "NAME IS THE ONLY THING THAT MATTERS AND THE ONLY THING YOU MAY NOT GUESS. Return a row ONLY "
    "when you can actually READ its name on this image. An icon you recognise but whose label you "
    "cannot read is NOT a row — leave it out. This read runs unattended over old footage and writes "
    "into the player's owned-item ledger, so a confident wrong name is permanent and an omission is "
    "not: the next session re-reads the same shelf.\n"
    "count = the stack number printed on the icon, or null when there is none. Never infer a count "
    "from how full the grid looks.\n"
    "kind: rune = a rune (El, Eth, Ist, Ber...). gem = a gem (chipped/flawed/perfect ruby, skull...). "
    "material = a crafting/upgrade material. item = anything else (armour, weapon, charm, jewel).\n"
    "conf = your own confidence 0.0-1.0 that the names you returned are what is on the image. Be "
    "honest and low rather than generous: two sessions must agree before anything is kept, so an "
    "unsure read costs nothing and a confidently wrong one costs the shelf.\n"
    # ── v1903 — `throwOut` WAS IN THE SCHEMA AND NOWHERE IN THE PROMPT ────────────────────────
    # It appeared exactly once, inside the JSON template, printed as `false`. Nothing told the
    # reader what it meant, when to set it, or that `throwWhy` existed at all — and vault_retro
    # consumes both, gates them behind a higher confidence floor and three separate recordings,
    # and rides them out to him as suggestions. An elaborate safety mechanism fed by a field
    # nobody was ever asked to fill. [[the-unjoined-end]]
    #
    # The definition below is deliberately NARROW, and the code does not rely on it: a grail name
    # is refused by vault_retro._grail_guard() whatever the reader says. Konyo decides how wide
    # "junk" should be; this is the floor, not his policy.
    "throwOut = true ONLY for an item that is plainly worthless: a WHITE or GREY base with no "
    "sockets and no magical text. Never for a named unique or set item, never for a rune, a gem, "
    "a jewel, a charm or a crafting material, and never because you do not recognise something. "
    'When you set it true, also give throwWhy = a short reason in your own words, e.g. "white '
    'base, no sockets". Default false. THERE IS NO UN-THROW IN DIABLO: a suggestion to bin '
    "something he wanted is the one mistake here that cannot be taken back, so when in doubt "
    "leave it false. His roster is checked again afterwards and a grail name is refused whatever "
    "you say.\n"
    "If this is NOT a {surface} panel, or you cannot read any name on it, return items EMPTY. An "
    "empty answer is recoverable; a wrong one is not."
)


CHRONICLE_READ_PROMPT = (
    "Image {path} = the in-game CHRONICLE (holy grail) panel of Diablo II Resurrected (RotW mod): a "
    "long scrollable list of item names where each row shows whether the player has FOUND it — "
    "bright/coloured text vs grey/dim, a tick, or a filled marker.\n"
    "Reply with STRICT JSON only, no markdown, no prose:\n"
    '{{"ledger":"{ledger}","found":[],"notFound":[],"sets":[],"printedFound":null,'
    '"printedTotal":null,"stateVisible":true,"wrongTab":false,"notChronicle":false,'
    '"foundAt":{{}},"droppedBy":{{}},"conf":0.0}}\n'
    "found = ONLY names whose found-state is VISIBLY positive. notFound = names you can read whose "
    "state is dim, empty or ambiguous.\n"
    # v1839 — "THIS IS NOT THE CHRONICLE" AND "I CANNOT JUDGE THESE ROWS" ARE DIFFERENT FACTS.
    # A reel is a screen recording: it opens and closes on his TV DIABLO console window and on
    # ordinary gameplay. Those frames are correctly refused — but they came back stateVisible=false,
    # the SAME answer as a legible Chronicle page whose rows could not be judged, so the refusal
    # count mixed healthy refusals with lost pages and could be read as neither. Opening six of his
    # refused frames settled it: three were the console window or gameplay (right to refuse), three
    # were legible sets pages carrying First Found dates (lost). One number, two opposite meanings.
    "notChronicle = true when the picture is not a Chronicle panel at all - gameplay, a stash, a "
    "menu, or the TV DIABLO console window. That is a different answer from a Chronicle page whose "
    "rows you cannot judge, and saying which costs nothing while guessing costs a page.\n"
    "If you cannot tell found from unfound ANYWHERE on this panel, set stateVisible=false and return "
    "found EMPTY. This read runs unattended over old footage, so a confident wrong page permanently "
    "mis-tallies a grail nobody is watching. An empty answer is recoverable; a wrong one is not.\n"
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
    "THE LEDGER YOU WERE ASKED FOR IS {ledger}. uniques = single unique items (Harlequin Crest, "
    "Windforce, Stormshield). sets = rows grouped under SET names (Tal Rasha's Wrappings, Immortal "
    "King). If the panel is the OTHER one, set wrongTab=true and return found empty — never tally "
    "set pieces as uniques or the reverse.\n"
    # v1566 — `complete` is READ in three places and was EMITTED by none of the reader lanes.
    # intake.js:691 reads g.complete === true, chronicle_retro.py:427 reads g.get("complete") is
    # True, and bible.html's chronicleApply expands a COMPLETE set into all its pieces (v1530).
    # Neither this lane nor the Grok one ever asked for it, so prop["completeSets"] was always
    # empty and v1530 has never fired once from a sweep. A page that says a set is done is one row
    # worth five, and it was being thrown away at the only point that could have captured it.
    'sets = only when ledger=sets: [{{"set":"<set name>","pieces":["<found piece>"],"complete":true|false}}].\n'
    'set `complete` true ONLY when the panel itself marks that set finished — never inferred from '
    'the pieces you happen to see.\n'
    # v1826 — A SET HEADING IS NOT A PIECE, and the readers confused the two about a quarter of the
    # time. Measured on his own swept evidence: of 16 set groups, 4 were keyed by something that is
    # not a set — "M'avina's True Sight", "M'avina's Tenet" and "Cleglaw's Claw" are PIECES, and
    # "Cathan's" is a truncation. It wrote no bad data (a heading that matches no set expands to
    # nothing, and the apply only ever wrote real roster pieces), but a quarter of the groups being
    # junk is a reader that has not been told what a heading looks like.
    # The tell is unambiguous on his frames, so it is spelled out rather than left to judgement.
    "A SETS page groups its rows under a set-name HEADING. The heading is centred, has NO item "
    "icon, NO `Dropped By:` line and NO `First Found:` line. Every PIECE row has all three. Put the "
    "HEADING in \"set\" and the rows beneath it in \"pieces\" — never a piece name in \"set\", and "
    "never a heading in \"pieces\". If you cannot see which heading a row belongs to, leave that "
    "row out rather than inventing a group for it.\n"
    "printedFound / printedTotal = the panel's own progress numbers if it shows any (\"243/403\", "
    "\"Found 108 of 135\") EXACTLY as printed, else null. They are checked against your own count as "
    "a second witness, so an honest mismatch is worth more than a flattering match.\n"
    "Read only rows you can actually see. Do not complete a set from memory or fill a page.\n"
    # v1819 — THE DATES THAT WERE ALWAYS ON THE PAGE. Konyo: "there is an option for newest found ...
    # so they know what they registered yesterday and whats new today". Checked against his own
    # 20-Aug frames first: every row carries its own `First Found:` stamp and a `Dropped By:` line,
    # and the sort control prints "Newest to Oldest" at the top right. The sweep was reading these
    # pages and keeping only the names, so nothing downstream could distinguish a FRESH find from
    # one that had simply never been read before — the question he is actually asking.
    # v1828 — `sort` IS GONE, because it never once arrived. Asked for on every chronicle read since
    # v1819 and returned EMPTY 2358 times out of 2358 - then tested directly against a frame that
    # plainly shows "Newest to Oldest" at its top right, which came back sort="" while correctly
    # returning four found names and four dates from the same picture. The field was plumbed end to
    # end; the readers simply never fill it.
    # It is not worth another attempt at the wording either, because the thing it was for is already
    # solved better: every row now carries its own `First Found:` stamp, so the ORDER of the list is
    # derivable from the data instead of read off a control. A prompt line that has never produced a
    # value is not free - it is paid for on every page of every sweep, and it reads to the next
    # person as a capability that exists.
    "foundAt = map each FOUND name -> its exact `First Found:` stamp, copied digit for digit, e.g. "
    '{{"Razorswitch":"08/20/2026, 00:49"}}. Omit any row whose stamp is hidden behind a tooltip or '
    "cut off at the panel edge, and NEVER infer one from a row's position. A missing stamp is "
    "recoverable; an invented one is a false find-date that nothing later re-reads.\n"
    "droppedBy = map each FOUND name -> the monster on its `Dropped By:` line. Omit what you cannot "
    "read.\n"
    "⚠ THE TWO TABS PRINT THOSE LINES IN OPPOSITE ORDER — measured on his frames, not assumed. On "
    "UNIQUES a row reads: name / `First Found: ...` / `Dropped By: ...`. On SETS it reads: name / "
    "`Dropped By: ...` / `First Found: ...`. Read each line by its LABEL, never by its position "
    "under the name, or every set piece gets a monster where its date belongs.\n"
    "conf = 0.0-1.0, your honest confidence in THIS page."
)


def _crop_answer_refused(raw, ledger_lane=True):
    """v1901 — ONE COPY, in chronicle_crop. The rule and every measurement behind it live in
    `chronicle_crop.crop_answer_refused`; this name stays because both crop routes below and the
    v1829 guards call it. A second copy of a refusal rule is how the two lanes drift apart, which
    is the exact defect v1901 was fixing when it moved this. [[copy-drift]]"""
    import chronicle_crop as _cc
    return _cc.crop_answer_refused(raw, ledger_lane=ledger_lane)


def claude_vault_read(image_path, surface, timeout=None):
    """One ownership panel, read on Konyo's Claude subscription, in vault_retro's `items` shape.

    v1785 — THE SEAM THAT WAS NEVER BUILT. vault_retro.sweep() reads resp["items"]; the vault sweep
    was wired to claude_chronicle_read, which returns found/notFound/sets and no items key, so the
    sweep spent real page reads, could never ground a single row, and then marked the reels swept.

    Returns {"items": [...], "conf": float} on a read, or {"note": "..."} on a refusal — the shape
    vault_retro already understands as NOT read, so a blocked lane can never be mistaken for an
    empty shelf. That is REG-180/181's rule, applied at birth rather than retrofitted.
    """
    if _is_throttled():
        return {"note": "reader throttled — not read"}
    _blocked = _sub_budget_check("oneshot")
    if _blocked:
        return {"note": "not read — %s" % _blocked}

    surface = str(surface or "stash").strip().lower()
    if os.environ.get("TV_STUB"):
        # the same TDD seam the other readers have: drivable end to end at zero vision cost
        try:
            man_path = os.environ.get("TV_STUB_MANIFEST") or os.path.join(HERE, "stub_manifest.json")
            with open(man_path, encoding="utf-8") as f:
                man = json.load(f)
        except Exception:
            man = {}
        raw = man.get(os.path.basename(image_path) + "#vault") or man.get("*#vault")
        if raw is None:
            return None
    else:
        ap = os.path.abspath(str(image_path or ""))
        if not os.path.isfile(ap):
            return None
        # CROP TO THE PANEL, for the reason v1780 measured on the chronicle lane: his frames are
        # full-desktop grabs and the panel is a fraction of them, so the rest is noise that costs
        # time AND blinds the read. stash_eye already owns this geometry, calibrated and locked on
        # his Mac — borrowed rather than re-derived, and it returns None when no honest band exists.
        _read_path = ap
        try:
            import stash_eye as _se
            from PIL import Image as _Im
            _im = _Im.open(ap).convert("RGB")
            _W, _H = _im.size
            # v1861 — THE INVENTORY IS THE PANEL ON THE RIGHT, and this cropped it to the left one.
            #
            # Every surface that was not a tally tab fell to the "runes" band — the LEFT stash
            # panel. For surface="stash" that is roughly right. For surface="inventory" it handed
            # the reader HIS STASH and asked it to read his inventory, so the honest answer was
            # always "this is not an inventory panel, items empty" — a lane that could never ground
            # a row, reported as an empty shelf. Measured on 6_1784984233446.jpg, the frame that is
            # exactly the stash+inventory template he asked for.
            #
            # The inventory band is not calibrated anywhere in stash_eye — the tally crops were
            # measured for the left panel only. So the honest move is NOT to invent one: read the
            # FULL FRAME for inventory. It costs more tokens and it is the only rectangle known to
            # contain the panel. [[unknown-stays-unknown]] — an uncalibrated band is not a band.
            _layout = surface if surface in ("runes", "gems", "materials") else "runes"
            _band = (None if surface == "inventory"
                     else _se.crops_for_aspect(_layout, float(_W) / float(_H)))
            if _band:
                _c = _im.crop((int(_W * _band[0]), int(_H * _band[1]),
                               int(_W * _band[2]), int(_H * _band[3])))
                if _c.width > 200 and _c.height > 200:
                    _cp = os.path.join(tempfile.gettempdir(), "tvd_vault_crop_%d.jpg" % os.getpid())
                    _c.save(_cp, quality=94)
                    _read_path = _cp
        except Exception:
            _read_path = ap
        raw = _oneshot(_read_path, GENIUS_MODEL,
                       timeout=float(timeout or 120),
                       prompt=VAULT_READ_PROMPT.format(path=_read_path, surface=surface),
                       raw_json=True)
        # the dual route v1780 proved out: a refused CROP gets one full-frame retry, so cropping
        # can only ever add reads. v1829 — "refused" now covers a crop that ANSWERS and refuses,
        # not only one that returns nothing (see _crop_answer_refused).
        if (_read_path != ap and _crop_answer_refused(raw, ledger_lane=False)
                and not _sub_budget_check("oneshot")):
            # same cap re-check as the chronicle route above — one budget check may not license two
            # reads now that the retry fires on a refusal rather than only on a crash.
            _full = _oneshot(ap, GENIUS_MODEL,
                             timeout=float(timeout or 120),
                             prompt=VAULT_READ_PROMPT.format(path=ap, surface=surface),
                             raw_json=True)
            # Only if it is actually BETTER. A full frame that also refuses must never overwrite
            # the crop's answer — a retry that can lose information is not a retry.
            if not _crop_answer_refused(_full, ledger_lane=False):
                raw = _full

    if raw is None:
        return None
    try:
        d = raw if isinstance(raw, dict) else json.loads(str(raw))
    except Exception:
        return {"note": "the reader did not return JSON — not read"}
    if not isinstance(d, dict):
        return {"note": "the reader did not return an object — not read"}
    items = d.get("items")
    if not isinstance(items, list):
        items = []
    # Pass rows through UNTOUCHED except for shape: normalize_item is vault_retro's job and it is
    # the thing that refuses a nameless row. Typing them here would put the contract in two places.
    out = [x for x in items if isinstance(x, dict)]
    try:
        conf = float(d.get("conf"))
    except Exception:
        conf = None
    return {"items": out, "conf": conf, "surface": surface}


def claude_chronicle_read(image_path, kind, timeout=None):
    """One chronicle page, read on Konyo's Claude subscription, in the v1510 shape.

    Returns None on any refusal/failure — never an empty page, for the same reason the Grok lane
    does: a dead lane must not read as "saw nothing"."""
    # v1774 — A THROTTLED READER MUST REFUSE OUT LOUD, NOT ANSWER EMPTY.
    # _note_slot_death() flips this when 2+ workers die inside 60s and its own docstring promises to
    # "SAY SO instead of silent empties" — but only the live heartbeat cap and a status chip ever
    # read the flag. The retro sweep did not, so during a throttle it kept calling, the readers
    # degraded to scene='gameplay', conf=None, names=[], and every layer downstream treated that as
    # a real answer: classify said "not a Chronicle page", the page read counted as read-with-no-
    # names, the sweep finished "successfully" with zero findings — and since v1766 the reels were
    # then MARKED SWEPT and never looked at again. Measured directly: three sweeps in a row returned
    # 39, then 22, then 0 names as the throttle deepened, and a frame that read chronicle/uniques
    # with 6 names came back gameplay/0 minutes later.
    # A `note` is the shape chronicle_retro already understands as "not read" — it counts as refused
    # rather than as an empty page, so nothing downstream mistakes a silence for an answer.
    if _is_throttled():
        return {"note": "reader throttled — not read"}
    # v1777 — a page the SUBSCRIPTION CAP refused is not a page that held nothing. This one already
    # returned None (its own contract), but saying WHICH refusal it was is the difference between
    # "your footage is empty" and "you are out of reads until the window rolls".
    _blocked = _sub_budget_check("oneshot")
    if _blocked:
        return {"note": "not read — %s" % _blocked}
    if os.environ.get("TV_STUB"):
        # the TDD seam: the sweep must be drivable end-to-end with zero vision cost, exactly like
        # the live loop is (TV_STUB, v711)
        try:
            man_path = os.environ.get("TV_STUB_MANIFEST") or os.path.join(HERE, "stub_manifest.json")
            with open(man_path, encoding="utf-8") as f:
                man = json.load(f)
        except Exception:
            man = {}
        raw = man.get(os.path.basename(image_path) + "#chronicle") or man.get("*#chronicle")
        if raw is None:
            return None
        _framing = "stub"   # v1901 — a stubbed read saw no pixels at all; say so rather than lie
    else:
        ap = os.path.abspath(str(image_path or ""))
        if not os.path.isfile(ap):
            return None
        ledger = "sets" if str(kind or "").endswith("sets") else "uniques"
        # ── v1780 — READ THE LIST, NOT THE LIVING ROOM ────────────────────────────────────────
        # His frames are 2940x1912 full-desktop grabs; the Chronicle list is 26% of that. The other
        # 74% is town, his character, the life orbs and the dock — and it does not merely cost time,
        # it BLINDS the read. Measured over six frames of his thorough reel, same reader, same day:
        #
        #     full frame : 0/6 pages read, 0 names, six "no-found-state" refusals
        #     list crop  : 5/6 pages read, 17 names, one refusal
        #
        # That is the whole difference between a sweep that finds his items and one that reports
        # empty footage. chronicle_template already measured this band on his own calibration film
        # (LIST_BAND, aspect-corrected by _scale_band_for_aspect) and used it only to CLASSIFY
        # frames — never to crop what gets read. The stash lane has cropped since v947 and its own
        # notes say chrome only becomes readable "via a deliberate crop + 3x upscale".
        #
        # DUAL ROUTE, accuracy first: if the crop comes back refused we retry the FULL frame, so
        # this can only add reads, never remove one. Upscaling was measured too and did not help on
        # top of the crop, so it is not done — the win is the framing, not the pixels.
        # v1901 — ONE CROP, SHARED WITH THE GROK LANE. This block used to live here alone, which
        # is precisely why the second lane never had it: a crop nobody else can call is a crop only
        # one witness gets. The band, the aspect correction and the fallback are in chronicle_crop.
        import chronicle_crop as _cc
        _read_path, _framing = _cc.list_crop(ap)
        raw = _oneshot(_read_path, GENIUS_MODEL,
                       timeout=float(timeout or 120),
                       prompt=CHRONICLE_READ_PROMPT.format(path=_read_path, ledger=ledger),
                       raw_json=True)
        # the dual route: a refused CROP gets one full-frame retry, so cropping can only add reads.
        # v1829 — "refused" now covers a crop that ANSWERS and refuses, which is what was denying
        # legible sets pages their second attempt. NOTE the correction in _crop_answer_refused: the
        # crop framing is NOT the cause — measured, the crop reads the canonical failing frame fine.
        # This buys a retry against a TRANSIENT refusal, and the source of that transience is open.
        if _read_path != ap and _crop_answer_refused(raw) and not _sub_budget_check("oneshot"):
            # v1845 — THE RETRY MUST ASK THE CAP AGAIN. The budget is checked once, at the top of
            # this read, and before v1829 the full-frame retry fired only on a hard crash, so one
            # check covered one read in practice. v1829 made the retry fire on a REFUSAL, which is
            # common, so a single budget check now licenses two reads on every refused page. Under
            # the subscription cap that is a bounded but systematic overrun, and the cap is the one
            # guard between a long sweep and his whole allowance.
            # Skipping the retry simply leaves the crop's answer standing, which is exactly the
            # pre-v1829 behaviour — an honest refusal rather than a read he could not afford.
            _full = _oneshot(ap, GENIUS_MODEL,
                             timeout=float(timeout or 120),
                             prompt=CHRONICLE_READ_PROMPT.format(path=ap, ledger=ledger),
                             raw_json=True)
            if not _crop_answer_refused(_full):
                raw = _full
                _framing = _cc.FULL   # v1901 — the page records the pixels that ANSWERED it
    try:
        import chronicle_retro as _cr
    except Exception:
        return None
    return _cr.normalize_page(raw, kind, "claude", framing=_framing)


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
        # v1188 — the Master Brain law (v948.17: "cap a single live read's in-flight time much
        # tighter" — LIVE_READ_TIMEOUT_S, default 35s) bounded the warm read AND its one-shot
        # fallback, but this THIRD call (fired on top of either of those, whenever a low-conf/
        # empty-loot read needs a second opinion) was still hardcoded at timeout=90 — inert
        # today only because FAST_MODEL==GENIUS_MODEL by default (see _maybe_genius's early-out
        # above), but the instant escalate is turned on (TV_MODEL_ESCALATE != TV_MODEL — exactly
        # the haiku→sonnet ladder these globals exist for) a single live claude_read() could
        # again hold the lane hostage for up to LIVE_READ_TIMEOUT_S + 90s ≈ 125s — WORSE than the
        # 66s stall that law was written to eliminate. Bound it by the same live-lane budget.
        better = _oneshot(ap, GENIUS_MODEL, timeout=LIVE_READ_TIMEOUT_S)
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
    # v1774 — see claude_chronicle_read: a throttled classify that answers "gameplay" is how a
    # whole reel gets skipped and then marked swept. None here means "no answer", which the sweep's
    # classifier() already treats as unknown rather than as a verdict.
    if _is_throttled():
        return None
    # v1777 — AND THE SAME DEFECT THROUGH THE OTHER DOOR: THE SUBSCRIPTION CAP.
    # _sub_budget_check is a circuit breaker protecting his account, and it works. What did not work
    # is the SHAPE of the refusal: _oneshot returns None when the cap is hit, and the parse below
    # then produced {"scene": "gameplay", "names": [], "conf": None} — a confident-looking verdict
    # that classify reads as "not a Chronicle page". Measured tonight: the cap sat at 250/250, every
    # read returned that dict in 0.0s, and a sweep "ran" for fifty minutes reading nothing while
    # reporting success. v1774 closed this for the throttle and left the budget door open, which is
    # the door we actually walked through.
    # v1778 — moved BELOW the G5 lane; see the guard just before the Claude worker call.
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
                "chronicleTab": _norm_chron_tab(rd.get("chronicleTab") or rd.get("chronicle_tab"), scene),
                "model": "stub", "mode": "stub", "escalated": False, "ms": 0}
    ap = _readable_frame(os.path.abspath(path), out_jpg)
    EMPTY = {"area": "", "scene": "gameplay", "names": [], "tz": [], "conf": None,
             "intent": "context", "stashTab": "",
             "model": FAST_MODEL, "mode": "empty", "escalated": False, "ms": 0}
    if not os.path.isfile(ap):
        print(f"  ⚠ image missing: {ap}")
        return EMPTY

    # ══ GROK EYES (G5) — REMOVABLE ════════════════════════════════════════════
    # Phase 2: shadow only (Claude result always returned). Phase 3: primary branch.
    # OFF/missing module → zero behavior change. See tv/G5_GROK_EYES_REMOVAL.md
    try:
        import g5_grok_eyes as _G5
    except Exception:
        _G5 = None
    if _G5 is not None:
        try:
            if _G5.is_primary():
                # Phase 3 path — only active when mode=primary + key
                _g5r = _G5.g5_vision_read(ap, prompt=READ_PROMPT.format(path=ap))
                if _g5r is not None:
                    if "intent" not in _g5r or not _g5r.get("intent"):
                        _g5r["intent"] = _intent_for(_g5r.get("scene"))
                    _g5r["stashTab"] = _norm_stash_tab(
                        _g5r.get("stashTab") or _g5r.get("stash_tab"), _g5r.get("scene"))
                    globals()["_LAST_RAW"] = str(_g5r.get("_raw_txt") or "")[:2048]
                    return _g5r
                # v1457 HONESTY (audit): G5 Grok Eyes is Konyo's MANDATED primary vision lane on
                # this Mac. When it fails, the read silently continued on Claude and the reason —
                # which g5_grok_eyes already recorded in _STATS["last_error"] ("grok CLI not on
                # PATH", "grok -p timeout", "no-json from grok -p", …) — never reached the console.
                # A swallowed failure in the PRIMARY lane reads as "Grok is working". Say WHY.
                _why = ""
                try:
                    _why = str((_G5.status().get("stats") or {}).get("last_error") or "")[:120]
                except Exception:
                    _why = ""
                ev("cap", "⚠ G5 primary vision returned None — Claude fallback"
                          + (f" · why: {_why}" if _why else " · no reason recorded"))
        except Exception as _g5e:
            try:
                ev("cap", f"⚠ G5 primary failed (Claude fallback): {_g5e}")
            except Exception:
                pass
    # ══ END GROK EYES (G5) ════════════════════════════════════════════════════

    t0 = time.time()
    # v1778 — THE CLAUDE CAP GATES THE CLAUDE PATH, AND ONLY IT. v1777 put this check at the top of
    # the function, above the G5 block — and Grok runs on its OWN quota
    # (g5_subscription_budget.json), so a full CLAUDE budget silently disabled the GROK primary eye.
    # A per-lane circuit breaker that takes down the other lane is worse than no breaker: it removes
    # the independent witness precisely when the main lane is struggling. Caught by code review.
    #
    # None (not EMPTY) is still the answer, because classifier() treats None as "no answer" while a
    # dict is the verdict "not a Chronicle page" — that shape is REG-181 itself. And the cap is
    # ANNOUNCED here, because returning early used to skip _oneshot_inner's ev()/journal_skip and
    # made the classify door quieter after the fix than before it.
    _blocked = _sub_budget_check("oneshot")
    if _blocked:
        try:
            ev("cap", _blocked)
            journal_skip("sub-budget", _blocked)
        except Exception:
            pass
        return None
    w = worker or _WORKER
    out_w = w.ask(READ_PROMPT.format(path=ap), timeout=LIVE_READ_TIMEOUT_S)
    if out_w is not None:
        globals()["_LAST_RAW"] = str(out_w)[:2048]   # v832 — THE THOUGHT, verbatim (single-reader compat)
        _raw_local = str(out_w)[:2048]
        parsed = _parse_read(out_w)
        if parsed is not None:
            parsed["_raw_txt"] = _raw_local   # v864 — raw travels WITH the result, no global race
        if parsed is not None:
            out = _maybe_genius(ap, parsed, t0, "warm") or EMPTY
            # ══ GROK EYES (G5) — shadow (never replaces Claude) ══
            try:
                if _G5 is not None and _G5.is_shadow():
                    def _g5_shadow_job(_p=ap, _c=out):
                        try:
                            _gr = _G5.g5_vision_read(_p, prompt=READ_PROMPT.format(path=_p))
                            _G5.g5_shadow_log(_c, _gr, _p)
                        except Exception:
                            pass
                    threading.Thread(target=_g5_shadow_job, daemon=True).start()
            except Exception:
                pass
            # ══ END GROK EYES (G5) ══
            return out
        ev("cap", "worker returned non-JSON — falling back to one-shot")
    else:
        ev("skip", "vision worker died (timeout/stream end) — one-shot for this read, re-warming behind it")
        _note_slot_death()   # v891 (Grok C1) — cascade detector
        _rewarm(w)  # v718 (Grok R10 pick #2) + v863: rewarm THIS reader's slot only, pool degrades soft
    try:
        # v948.17 — same lane-block cap applies to the one-shot fallback: a wedged warm
        # worker must not be followed by ANOTHER unbounded (90s) attempt on the live lane.
        parsed = _oneshot(ap, FAST_MODEL, timeout=LIVE_READ_TIMEOUT_S)
        if parsed is None:
            return EMPTY
        out = _maybe_genius(ap, parsed, t0, "oneshot") or EMPTY
        # ══ GROK EYES (G5) — shadow oneshot path ══
        try:
            if _G5 is not None and _G5.is_shadow():
                def _g5_shadow_job2(_p=ap, _c=out):
                    try:
                        _gr = _G5.g5_vision_read(_p, prompt=READ_PROMPT.format(path=_p))
                        _G5.g5_shadow_log(_c, _gr, _p)
                    except Exception:
                        pass
                threading.Thread(target=_g5_shadow_job2, daemon=True).start()
        except Exception:
            pass
        # ══ END GROK EYES (G5) ══
        return out
    except subprocess.TimeoutExpired:
        ev("cap", f"vision timed out ({LIVE_READ_TIMEOUT_S:.0f}s) — if this repeats, run: python3 tv/tv_diablo.py --test <img>")
        print(f"  ⚠ vision timed out ({LIVE_READ_TIMEOUT_S:.0f}s)")
        return EMPTY
    except Exception as e:
        ev("cap", f"read failed: {e}")
        print(f"  ⚠ read failed: {e}")
        return EMPTY


# ── v926 SECOND LOOK — the reader's second-layer accuracy pass ──────────────────────────────
_VERIFY_Q = deque(maxlen=32)   # jobs: {"fid","names","n","sid","scene","cap_ms"}


def verify_read(path, prior_names, worker=None, timeout=75):
    """Re-read the SAME archived screenshot to correct a prior read. Returns
    {confirm, missed, not_present, conf} or None. Honours TV_STUB (keyed '<base>#verify')."""
    if os.environ.get("TV_STUB"):
        try:
            man_path = os.environ.get("TV_STUB_MANIFEST") or os.path.join(HERE, "stub_manifest.json")
            with open(man_path, encoding="utf-8") as f:
                man = json.load(f)
        except Exception:
            man = {}
        rd = man.get(os.path.basename(path) + "#verify") or man.get("*#verify") or {}
        return {"confirm": rd.get("confirm", list(prior_names)),
                "missed": rd.get("missed", []), "not_present": rd.get("not_present", []),
                "conf": rd.get("conf", 1.0)}
    ap = _readable_frame(os.path.abspath(path))
    if not os.path.isfile(ap):
        return None
    w = worker or _WORKER
    try:
        out = w.ask(VERIFY_PROMPT.format(path=ap, prior=json.dumps(list(prior_names))), timeout=timeout)
    except Exception:
        return None
    if out is None:
        return None
    try:
        txt = str(out)
        i, j = txt.find("{"), txt.rfind("}")
        d = json.loads(txt[i:j + 1]) if i >= 0 and j > i else None
    except Exception:
        d = None
    if not isinstance(d, dict):
        return None
    return {"confirm": [x for x in (d.get("confirm") or []) if _itemish(x)],
            "missed": [x for x in (d.get("missed") or []) if _itemish(x)][:5],
            "not_present": [x for x in (d.get("not_present") or []) if _itemish(x)],
            "conf": float(d.get("conf") or 0.0)}


def _verify_apply(job, worker=None, timeout=75):
    """v926 — run one verify job: re-read the frame, compute the delta, journal a `lane=verify`
    beat on a distinct sub-frame id (so the funnel's exactly-once holds), and route the
    correction through the SAME lifecycle pipes. REMOVE (misread) is the default correction;
    ADD (missed) is conservative — only high-confidence, clearly-readable names."""
    fid = str(job.get("fid") or "")
    prior = [x for x in (job.get("names") or []) if _itemish(x)]
    if not fid or not prior:
        return None
    src = os.path.join(HIST_DIR, fid + ".jpg")
    if not os.path.isfile(src):
        return None
    v = verify_read(src, prior, worker=worker, timeout=timeout)
    if not v:
        return None
    conf = v.get("conf") or 0.0
    # v926-R4 (Grok) — REMOVE-ONLY second look: only UN-tally a name that (a) the verify rejects,
    # (b) was in the original read, AND (c) was actually VAULTED by that read. ADD is deferred to
    # a future pass-3 — force-vaulting a "missed" hallucination is a permanent false +1 footgun.
    _vaulted = {str(x).lower() for x in (job.get("vaulted") or [])}
    _priorset = {str(x).lower() for x in prior}
    remove = [x for x in v.get("not_present", [])
              if conf >= 0.7 and str(x).lower() in _priorset and str(x).lower() in _vaulted]
    missed = [x for x in v.get("missed", [])]   # surfaced for the debugger; NOT applied at pass-2
    add = []   # ADD off until pass-3 (scene gate + readable-text proof) owns it
    # v926 — the board ingests reads by ts > SEEN, so a verify beat MUST carry ts=now (else the
    # board skips it as already-seen). captureTs stays the ORIGINAL frame clock so the SIM keeps
    # the second look pinned to the exact frame it re-checked.
    cap_ms = int(job.get("cap_ms") or time.time() * 1000)
    now_ms = int(time.time() * 1000)
    if not remove:
        # a clean confirm (or a low-conf/unvaulted rejection we won't act on) — journal the
        # second look anyway so the debugger shows the read was verified. `missed` is surfaced
        # for the human/pass-3, never tallied here.
        _journal({"ts": now_ms, "captureTs": cap_ms, "completedTs": now_ms, "n": job.get("n"),
                  "scene": job.get("scene") or "loot", "names": [], "sessionId": job.get("sid") or SESSION_ID,
                  "frameId": fid + "#v", "lane": "verify", "mode": "verify",
                  "verify": {"confirm": v.get("confirm", []), "missed": missed, "not_present": [], "conf": conf},
                  "vault_names": [], "unvault_names": [],
                  "note": ("✓ second look — read confirmed" if not missed else "✓ second look — %d maybe-missed (flagged)" % len(missed))})
        return {"delta": 0, "add": [], "remove": [], "missed": missed}
    # REMOVE routes through the SAME board pipe: a lane=verify beat with unvault_names decrements
    # the funnel/vault exactly like a real correction (distinct #v frameId → exactly-once holds).
    _journal({"ts": now_ms, "captureTs": cap_ms, "completedTs": now_ms, "n": job.get("n"),
              "scene": job.get("scene") or "loot",
              "names": [], "sessionId": job.get("sid") or SESSION_ID,
              "frameId": fid + "#v", "lane": "verify", "mode": "verify",
              "verify": {"confirm": v.get("confirm", []), "missed": missed, "not_present": remove, "conf": conf},
              "vault_names": [], "unvault_names": remove,
              "note": "🔎 second look — corrected −%d (conf %.2f)" % (len(remove), conf)})
    ev("cap", "second look @%s — −%d misread (conf %.2f)" % (fid, len(remove), conf))
    return {"delta": len(remove), "add": [], "remove": remove, "missed": missed}


def _verify_drain(worker=None, budget=1, timeout=75, deadline=None):
    """Drain up to `budget` verify jobs. Called from the main loop's idle gap (default: one
    job, no deadline) AND — v1179 CLOSER — from `_pool_shutdown` with a `deadline` so a job
    queued for the last read(s) before session close still gets its second-look correction
    instead of vanishing with the queue when the process exits.

    v1200 — `deadline` is a time.monotonic() value (the caller, `_pool_shutdown`, computes it
    that way) specifically so a backward wall-clock jump mid-shutdown can't turn 'spend the
    leftover shutdown budget' into 'wait out however long the clock jumped'."""
    if not VERIFY_ON:
        return
    n = 0
    while _VERIFY_Q and n < budget:
        if deadline is not None and time.monotonic() >= deadline:
            break   # out of shutdown budget — leave the rest un-drained rather than overrun
        try:
            _verify_apply(_VERIFY_Q.popleft(), worker=worker, timeout=timeout)
        except Exception as e:
            try: ev("skip", "verify failed: %s" % e)
            except Exception: pass
        n += 1


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
    globals()["_SESSION_T0_MS"] = int(time.time() * 1000)   # v885 (Grok #2) — reel fold spans from BOOT, not first read
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
    import queue as _qmod
    globals()["_JQ"] = _qmod.Queue()
    threading.Thread(target=_journal_writer_loop, daemon=True, name="tv-journal").start()   # v879 — Grok A(a): one ordered writer
    threading.Thread(target=_state_saver_loop, daemon=True, name="tv-statesave").start()    # v879 — write-behind 1s
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
    if ROBOT_MODE:
        print(f"📺 TV DIABLO {VERSION} — ROBOT (TV_ROBOT=1) · pool={POOL_N} · film ~{_FILM_FPS}fps")
        print(f"   cadence: gap={MIN_GAP_S}s · heartbeat={HEARTBEAT_S}s · priority={PRIORITY_GAP_S}s")
    else:
        print(f"📺 TV DIABLO {VERSION} — AUTO INTAKE · Robot FROZEN · pool=1 · " + ("⚡ LIGHT reader" if LIGHT_MODE else f"film ~{_FILM_FPS}fps"))
        print(f"   product: pause on stash/loot → same AI as Tools 📸 (runes/gems/materials/vault)")
        print(f"   cadence: settle gap={MIN_GAP_S}s · no continuous heartbeat")
        print(f"   unlock robot later: TV_ROBOT=1 (frozen until playable unfreeze gate)")
    print(f"   bridge: http://127.0.0.1:{PORT}/state  ·  mode: {'watch (Windows frames)' if WATCH_MODE else 'mac screencapture'}")
    print("   capture: AUTO (pins D2R.exe only — never CrossOver Home / Battle.net)")
    print(f"   models: fast={FAST_MODEL} · genius={GENIUS_MODEL}")
    _film_on = (not LIGHT_MODE) or str(os.environ.get("TV_FILM", "0")).strip().lower() in ("1", "true", "yes", "on")
    if LIGHT_MODE:
        print(f"   ⚡ LIGHT reader — screenshot every ~{POLL_S:.1f}s · film OFF · OCR OFF · 1 claude · plays nice with the game")
        print("      (heavy cinematic capture for the SIM debugger: TV_LIGHT=0)")
    else:
        print(f"   film: live ~{_FILM_FPS}fps · SIM {_FOOTAGE_FPS}fps · max {FILM_MAX_PX}px · q{FILM_JPEG_Q}")
    ocr_tag = "ON " + OCR_BIN if _OCR.available() else "OFF"
    print(f"   ocr lane: {ocr_tag}")
    if ROBOT_MODE:
        print("   tip: ROBOT lane — continuous reads are the truth; stash-pause intake ALSO fires (governed by the debt law)")
    else:
        print("   tip: open Runes/Gems/Materials/stash and PAUSE — intake fires once per settle")
    print("   in the bible: SESSIONS tab → ON AIR. Ctrl-C to stop.\n")
    ev("boot", "product=" + ("robot" if ROBOT_MODE else "auto-intake") + " · robot_frozen=" + ("0" if ROBOT_MODE else "1"))
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
                # v1431 — Windows: prefer eye.jpg / live.png (always real images) before BMP;
                # path spaces + BMP→OCR cold paths used to log "ocr warm failed" every boot.
                jp = os.path.join(FRAMES, "read.jpg")
                probe = jp if os.path.isfile(jp) else None
                if not probe:
                    for cand in (
                        os.path.join(FRAMES, "eye.jpg"),
                        os.path.join(FRAMES, "live.png"),
                        os.path.join(FRAMES, "live.bmp"),
                    ):
                        if os.path.isfile(cand):
                            probe = cand
                            break
                if probe:
                    r = _OCR.read(probe, timeout=5.0 if sys.platform.startswith("win") else 3.0)
                    if r is not None:
                        ev("boot", f"ocr warm — Vision ready ({r.get('ms', '?')}ms probe)")
                    else:
                        # soft: not a fault lamp — deep lane still works
                        ev("boot", "ocr warm soft-miss — deep lane armed (fast lane may lag first settle)")
                else:
                    ev("boot", "ocr warm skipped — no frame yet (will arm on first capture)")
            except Exception as e:
                ev("boot", f"ocr warm soft-error — continuing ({type(e).__name__})")
        threading.Thread(target=_warm_ocr, daemon=True).start()
        threading.Thread(target=_text_eye_loop, daemon=True, name="tv-text-eye").start()
        ev("boot", "👁‍🗨 text eye armed — new on-screen text triggers priority reads (TV_TEXT_EYE=0 to disable)")
    else:
        # v927.2 — say WHY the fast lane is off: the v925 LIGHT default disables it even
        # when the binary exists (chased as a phantom "never compiled" for days).
        if not OCR_ENABLED:
            ev("skip", "ocr lane off (LIGHT default) — set TV_OCR=1 to arm the fast lane")
        else:
            ev("skip", "ocr binary missing — Claude-only until tv/bin/ocr_mac is built")

    frame = os.path.join(FRAMES, "live.bmp")
    # v927.3 — boot with a clean slate: a stale frame from a previous session (e.g. the
    # TCC-denied wallpaper era) kept showing as the board preview while the eye was
    # dormant — repeatedly read as "capture still broken". Missing frames render as the
    # normal STANDBY/IDLE splash; stale photos lie.
    for _stale in (frame, os.path.join(FRAMES, "eye.jpg")):
        try:
            if os.path.isfile(_stale) and os.path.getmtime(_stale) < time.time() - 30:
                os.remove(_stale)
        except OSError:
            pass
    # v870 — last_read_t starts NOW, not 0: the heartbeat's `and last_read_t` guard meant a
    # constant-motion session (his farm video, run 2) stayed BLIND until the first settle read.
    last_md5, stable, last_sent_md5, last_read_t, reads = None, 0, None, time.time(), 0
    peak = 0.0            # recent max motion while hunting
    priority = False      # hard motion seen since last read → short gap + 1-tick settle
    empty_streak = 0
    named_until = 0.0     # boost interest after a named hit

    def _launch_vision(snap_src, cur_snap, n_this, fid_this, interest_this, used_priority, read_ts,
                       rid_override=None):
        """v863 READER POOL — one reader ACT on ITS OWN worker + PRIVATE snap/read files. Builds
        the job (captureTs, origin, dispatch, sig) at fire time and carries it through to the
        ordered apply. Acquires a free reader id; the main loop gates on a free slot.

        v948.17 (Grok P1-4) — rid_override bypasses the pool entirely: it's how the stall-drain
        sweep gets a genuinely PARALLEL worker (`_stall_worker()`) even when every normal pool
        slot is busy. The override id is never returned to `_pool_free` (it isn't a pool member),
        so it can never leak into ordinary live dispatch."""
        global _VISION_BUSY, _STALL_BUSY
        import shutil
        if rid_override is not None:
            rid = rid_override
            _STALL_BUSY = True
        else:
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
                            _journal(dict(prec))   # v886 (Konyo: 'reads must be SYNCED') — a
                            # counted read that never journals can never appear in the SIM reel;
                            # the provisional flag travels so the theatre shows the fast lane honestly.
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
                _job_worker = _stall_worker() if rid_override is not None else _WORKERS[rid]
                rd = claude_read(snap_path, worker=_job_worker, out_jpg=read_jpg)
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
                    if rid_override is None and rid not in _pool_free:
                        _pool_free.append(rid); _pool_free.sort()
                    _VISION_BUSY = len(_in_flight) >= 1
                if rid_override is not None:
                    globals()["_STALL_BUSY"] = False
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
                   empty_s=0, named_s=0, ap_mode="", interest_parts=None, rid_override=None,
                   cap_ts_override=None):
        """ONE AI reader arm: settle or queue drain → shared last_read_t + dual-lane.

        v1187 — captureTs join law (A0 fix, 2026-07-21, applied here too): a queue/backlog
        drain reads a snapshot that was captured EARLIER (held while readers were busy, up to
        SETTLE_QUEUE_STALE_MS), but this function used to stamp it with `time.time()` at DRAIN
        time regardless — the receipt-landing time, not the frame's capture time. Every queue
        drain caller already tracks the entry's real capture clock as `ts` (that's exactly what
        `gap_ms` below is computed from) but never carried it into the frame_id/captureTs that
        the retro debugger actually joins on. cap_ts_override lets a drain caller pass that real
        clock through; live/fresh reads (no override) keep the old now() stamp unchanged."""
        nonlocal last_read_t, last_sent_md5, reads, peak, priority
        soft_over = reads - SESSION_CAP
        if soft_over >= 0:
            time.sleep(min(30.0, 6.0 + soft_over * 0.05))
        last_read_t, last_sent_md5 = time.time(), sig
        globals()["_LAST_EMIT_SIG"] = sig
        reads += 1
        read_ts = _resolve_read_ts(cap_ts_override)
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
        used = _launch_vision(snap_src, sig, reads, frame_id, interest_this, used_priority, read_ts,
                              rid_override=rid_override)
        if "queue" in origin:
            peak = 0.0
            priority = False
        return used

    while True:
        # v926.2 — adaptive sleep: long during active play (back off, don't stutter the game),
        # responsive when settled. _ADAPT_GAP is set from motion at the end of each iteration.
        # v1438 — Windows smooth: when a deep read is in flight, back off the sensor a bit so
        # capture + control UI get CPU (baby-bottom: no hitch mid-reading).
        _gap = float(globals().get("_ADAPT_GAP", POLL_S) or POLL_S)
        if sys.platform.startswith("win") and globals().get("_VISION_BUSY"):
            _gap = max(_gap, min(2.8, _gap * 1.4))
        time.sleep(_gap)
        # ── straggler flush + queue drain: freezes held while readers were busy ──
        try: _order_drain()
        except Exception: pass
        # v944 SECOND EYE AS SWEEPER (Konyo: "calibrate the first and second brain to catch
        # these BEFORE KAI") — the idle gap (worker free, no fresh live settle waiting) belongs
        # FIRST to the un-read text-eye backlog: freezes the newest-wins live drain skipped past.
        # The second eye reads that missed-text DURING the session, before verify re-checks and
        # before seal. Debt/pacing laws hold: never steal a live slot, one freeze at a time.
        try:
            if _vision_in_flight_n() < POOL_N and not _SETTLE_QUEUE:
                _swept = False
                _bl = _text_eye_backlog_pop()
                if _bl is not None:
                    if _in_flight_has_sig(_bl["sig"]):
                        _settle_file_del(_bl)   # this exact view is already on a reader
                    else:
                        _bused = _fire_read(
                            "text-eye-sweep-queue", _bl["path"], _bl["sig"],
                            _bl.get("interest", 0.9), True,
                            note="second eye — swept un-read text-eye backlog",
                            gap_ms=max(0, int(time.time() * 1000) - _bl.get("ts", 0)),
                            ap_mode="sweep-drain",
                            cap_ts_override=_bl.get("ts"),
                        )
                        if _bused != _bl["path"]:
                            _settle_file_del(_bl)
                    _swept = True
                # verify re-checks take the gap ONLY after the sweep backlog is clear
                if not _swept and VERIFY_ON and _VERIFY_Q:
                    _verify_drain(worker=_WORKER, budget=1)
            elif _stall_drain_ready():
                # v948.17 (Grok P1-4) — every normal slot is busy AND the oldest in-flight
                # read has been stuck past STALL_DRAIN_S: the old gate above will NEVER open
                # for this session (a hung live read is not an idle gap). Drain the backlog
                # anyway, on the dedicated PARALLEL stall worker — never on the live reader.
                _bl2 = _text_eye_backlog_pop()
                if _bl2 is not None:
                    if _in_flight_has_sig(_bl2["sig"]):
                        _settle_file_del(_bl2)   # this exact view is already on a reader
                    else:
                        _stall_ms = _live_stall_ms()
                        _bused2 = _fire_read(
                            "text-eye-sweep-stall", _bl2["path"], _bl2["sig"],
                            _bl2.get("interest", 0.9), True,
                            note=f"second eye — parallel stall-drain (live stalled {_stall_ms/1000:.0f}s)",
                            gap_ms=max(0, int(time.time() * 1000) - _bl2.get("ts", 0)),
                            ap_mode="stall-drain",
                            rid_override=_STALL_RID,
                            cap_ts_override=_bl2.get("ts"),
                        )
                        if _bused2 != _bl2["path"]:
                            _settle_file_del(_bl2)
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
                cap_ts_override=_q.get("ts"),
            )
            if used != _q["path"]:
                try: os.remove(_q["path"])
                except Exception: pass
            _drained_any = True
        if _drained_any:
            continue
        # v926.2 DORMANT-WHEN-NO-GAME (Konyo, acceptance day: "i cant open my game... it needs to
        # be smoother and more optimized"). For most of a launch the D2R window is missing. Do the
        # CHEAP Quartz window check FIRST, and while there's no game SKIP the expensive full-screen
        # capture entirely and idle longer. This stops the agent grabbing the whole screen every
        # ~2s while you're trying to launch — which burned CPU and fought the game's own render.
        if not WATCH_MODE and not os.environ.get("TV_STUB"):
            _ng = time.time()
            if _ng >= float(globals().get("_GAME_CHECK_DUE", 0.0) or 0.0):
                globals()["_GAME_CHECK_DUE"] = _ng + 1.5
                if _game_window_present():
                    globals()["_GAME_MISS_SINCE"] = 0.0
                    if globals().get("_AI_PAUSED"):
                        ev("cap", "🎯 D2R window found — AI reads live again")
                        print("  🎯 D2R window found — AI reads live again")
                    _set_game_gate(True, "")
                else:
                    # v927.4 DEBOUNCE (Konyo mid-session: "diablo ii window not open — but
                    # obviously it is"). CGWindowListCopyWindowInfo intermittently returns an
                    # incomplete list for CrossOver fullscreen, so a single bad poll used to
                    # tear the board down to the WATCHING/HOLD splash and pause reads for
                    # seconds at a time. One miss means nothing: keep the gate, the capture
                    # and the preview rolling; go dormant only after the window stays gone
                    # for a full grace window (genuine game exit still detected in ~6s).
                    _ms = float(globals().get("_GAME_MISS_SINCE", 0.0) or 0.0)
                    if not _ms:
                        globals()["_GAME_MISS_SINCE"] = _ng
                    elif (_ng - _ms) >= 6.0:
                        _msg = "D2R window missing — open Diablo II: Resurrected (in-game, not only Battle.net) for live reads"
                        if not globals().get("_AI_PAUSED"):
                            ev("cap", "⏸ " + _msg)
                            print("  ⏸ " + _msg)
                        _set_game_gate(False, _msg)
                        if _ng >= float(globals().get("_NOGAME_SKIP_DUE", 0.0) or 0.0):
                            globals()["_NOGAME_SKIP_DUE"] = _ng + 30.0
                            try: journal_skip("no-game", "D2R window not found — AI dormant (no capture)")
                            except Exception: pass
            if globals().get("_AI_PAUSED"):
                beat("hold", 0.0)
                _AP.update({"mode": "hold", "interest": 0.0, "peak": 0.0, "priority": False})
                time.sleep(3.0)   # DORMANT — no full-screen capture while there is no game
                continue
        if WATCH_MODE:
            # v784 — Windows capture half reports pin status via cap_target.json
            _refresh_cap_target_from_disk()
            f = newest_watched_frame()
            if not f: continue
            frame = f
            # v879/v897 — WINDOWS FOOTAGE PARITY: archive eye.jpg on FOOTAGE_INTERVAL_S (1fps).
            # v1428 — FOOTAGE STARVE 0.4fps live proof: allow eye age ≤5s (was 3s) and always
            # stamp _FOOTAGE_WHY + use promote-safe archive helper when available.
            try:
                _weye = os.path.join(FRAMES, "eye.jpg")
                _wnow = time.time()
                _wiv = FOOTAGE_INTERVAL_S
                if os.path.isfile(_weye) and (_wnow - os.path.getmtime(_weye)) < 5.0 \
                        and _wnow >= globals().get("_FOOTAGE_DUE", 0.0):
                    try:
                        _archive_footage_copy(_weye, _wnow, why="win-eye")
                    except Exception:
                        globals()["_FOOTAGE_DUE"] = max(globals().get("_FOOTAGE_DUE", 0.0) + _wiv, _wnow - (_wiv - 0.01)) \
                            if globals().get("_FOOTAGE_DUE") else _wnow + _wiv
                        import shutil as _shwz
                        _whd = HIST_DIR
                        os.makedirs(_whd, exist_ok=True)
                        if _shwz.disk_usage(_whd).free / 1e9 >= MIN_FREE_GB:
                            _FOOT_TIMES.append(_wnow)
                            globals()["_FOOTAGE_WHY"] = "win-eye-copy"
                            _shwz.copyfile(_weye, os.path.join(_whd, "f_%d.jpg" % int(_wnow * 1000)))
            except Exception:
                pass
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
                        # v946.4 (Konyo: "the settings tab keeps popping up every launch though the
                        # grant is done") — capture_mac ALSO fails when D2R simply isn't in the window
                        # list (the 'waiting' state), not only on a missing grant. Only blame + OPEN
                        # the Screen Recording settings when the grant is ACTUALLY missing; a closed or
                        # unfocused D2R must never pop System Settings. screen_recording_ok() returns
                        # True instantly (no dialog) when already granted.
                        _sr_ok = True
                        try:
                            _sr_ok = screen_recording_ok()
                        except Exception:
                            _sr_ok = True
                        if not _sr_ok:
                            try: open_screen_recording_settings()
                            except Exception: pass
                            ev("cap", "⚠ Screen Recording not granted — tick Python / TV DIABLO in System Settings → Privacy → Screen Recording, then RESTART")
                        else:
                            ev("cap", "waiting for the Diablo II window — Screen Recording is granted; open & focus D2R")
                    else:
                        ev("cap", "⚠ capture still failing — is the Diablo II window open & focused?")
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
        # v926.2 — adaptive next-gap: back off capture during active play, stay responsive when
        # settled so a pause on loot/stash is caught quickly. Never back off while a settle is
        # pending (we want to confirm it and fire the read).
        globals()["_ADAPT_GAP"] = PLAY_GAP_S if (motion >= MOTION_PEAK and not _SETTLE_QUEUE) else POLL_S
        # v899 — NO D2R WINDOW: film may keep running, but AI reads stay OFF and the UI
        # shouts to open the game. Prevents 400-read desktop burn while working.
        _now_g = time.time()
        if _now_g >= float(globals().get("_GAME_CHECK_DUE", 0.0) or 0.0):
            globals()["_GAME_CHECK_DUE"] = _now_g + 1.2
            _gok = _game_window_present()
            if _gok:
                globals()["_GAME_MISS_SINCE"] = 0.0
                if globals().get("_AI_PAUSED"):
                    ev("cap", "🎯 D2R window found — AI reads live again")
                    print("  🎯 D2R window found — AI reads live again")
                _set_game_gate(True, "")
            else:
                # v927.4 DEBOUNCE — same grace as the dormant lane: one flaky Quartz poll
                # mid-play must not pause reads or flash the missing banner.
                _ms = float(globals().get("_GAME_MISS_SINCE", 0.0) or 0.0)
                if not _ms:
                    globals()["_GAME_MISS_SINCE"] = _now_g
                elif (_now_g - _ms) >= 6.0:
                    _msg = "D2R window missing — open Diablo II: Resurrected (in-game, not only Battle.net) for live reads"
                    if not globals().get("_AI_PAUSED"):
                        ev("cap", "⏸ " + _msg)
                        print("  ⏸ " + _msg)
                    _set_game_gate(False, _msg)
                    # rare skip ticks so SIM shows why the night was quiet (not every poll)
                    if _now_g >= float(globals().get("_NOGAME_SKIP_DUE", 0.0) or 0.0):
                        globals()["_NOGAME_SKIP_DUE"] = _now_g + 30.0
                        try:
                            journal_skip("no-game", "D2R.exe window not found — AI paused")
                        except Exception:
                            pass
        if globals().get("_AI_PAUSED"):
            beat("hold", motion)   # not "watching" — source-shape tests lock the real watch→heartbeat path
            last_md5 = cur
            peak = 0.0
            priority = False
            stable = 0
            _AP.update({"mode": "hold", "interest": 0.0, "peak": 0.0, "priority": False})
            continue
        # loading screens between zones are static + near-black — they settle but hold nothing
        # readable. v1379 B5-lite: on ENTERING the loading phase, stamp a local transition row
        # (0 vision cost) so LIVE/native flips to ENTERING <area> instead of stuck "gameplay".
        # Continuous near-black only beats "loading" after that one stamp — no journal spam.
        if sum(cur) / max(1, len(cur)) < 14:
            entering_load = _BEAT.get("phase") != "loading"
            if entering_load:
                note = transition_note(LAST_AREA, reads)
                ev("transition", f"⏳ {note} · near-black loading (local · 0 vision)")
                print(f"  ⏳ {note}  [near-black · 0ms]")
                t_ts = int(time.time() * 1000)
                try:
                    t_fid = archive_read_frame(frame, reads + 1, t_ts)
                except Exception:
                    t_fid = ""
                try:
                    _journal({"ts": t_ts, "n": reads + 1, "scene": "transition", "names": [],
                              "area": "", "frameId": t_fid, "note": note,
                              "transition_from": LAST_AREA, "ms": 0,
                              "mode": "near-black", "lane": "known", "sessionId": SESSION_ID})
                except Exception:
                    pass
                try:
                    with _state_lock:
                        st = _load()
                        st["reads"].append({
                            "ts": t_ts, "names": [], "n": reads + 1, "area": "",
                            "scene": "transition", "tz": [], "ms": 0,
                            "mode": "near-black", "lane": "known", "model": "local",
                            "conf": 1.0, "intent": "context",
                            "transition_from": LAST_AREA, "note": note,
                            "frameId": t_fid, "sessionId": SESSION_ID,
                            "escalated": False, "interest": 0.0, "priority": False,
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
                except Exception:
                    pass
                last_read_t = time.time()
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

        # v901 — HEARTBEAT dual-lane is ROBOT-only (FROZEN by default). Auto Intake waits for settle.
        if ROBOT_MODE and (_vision_in_flight_n() < POOL_N) and (_heartbeat_in_flight_n() < _heartbeat_cap()) \
                and last_read_t and (time.time() - last_read_t) >= HEARTBEAT_S and not _SETTLE_QUEUE \
                and not _in_flight_has_sig(cur):
            _hb_gap = int((time.time() - last_read_t) * 1000)
            reads += 1
            read_ts = int(time.time() * 1000)
            frame_id = archive_read_frame(frame, reads, read_ts)
            _hb_static = sig_diff(cur, last_sent_md5) <= SETTLE if last_sent_md5 else False
            ev("heartbeat", f"💓 heartbeat · {_hb_gap/1000:.1f}s since last · dual-lane #{reads} · pool {_vision_in_flight_n()}/{POOL_N}"
               + (" · static re-sample" if _hb_static else ""))
            print(f"  💓 heartbeat read #{reads} — {_hb_gap/1000:.1f}s since last · pool {_vision_in_flight_n()}/{POOL_N}")
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
                                          "note": "ROBOT forced read every %.1fs" % HEARTBEAT_S}
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
            last_read_t = time.time()   # v897 — known transitions count toward 1–2s cadence
            peak = 0.0
            priority = False
            continue
        gap = PRIORITY_GAP_S if priority else MIN_GAP_S
        if time.time() - last_read_t < gap:
            if stable == need_ticks:
                ev("skip", f"settled, but only {int(time.time()-last_read_t)}s since last read (gap {gap}s · {'PRIORITY' if priority else 'cruise'})")
                journal_skip("gap-wait", f"{int(time.time()-last_read_t)}s since last · gap {gap}s")   # v880 A2.8
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


def _text_eye_worthy(name):
    """v1379 — STRICTER than _itemish. Text-eye fires a full Sonnet subscription read;
    OCR garble like 'haTrng1.. Lobby' / 'ING THe R' / \"'Ii'\" must NEVER open that valve.
    Real item names are clean letter words (optionally multi-word); bare runes pass."""
    t = str(name or "").strip().strip("'\"`").strip()
    if not t:
        return False
    lo = t.lower()
    _RUNES = {"el","eld","tir","nef","eth","ith","tal","ral","ort","thul","amn","sol","shael",
              "dol","hel","io","lum","ko","fal","lem","pul","um","mal","ist","gul","vex","ohm",
              "lo","sur","ber","jah","cham","zod"}
    if lo in _RUNES or lo.replace(" rune", "").strip() in _RUNES:
        return True
    if not _itemish(t):
        return False
    # reject digit-heavy leetspeak / dotted OCR trash
    if sum(c.isdigit() for c in t) >= 1 and sum(c.isalpha() for c in t) < 8:
        return False
    if ".." in t or ",," in t:
        return False
    # pure letter words only (no leftover punctuation)
    words = [w for w in "".join(c if c.isalpha() or c == " " or c == "-" else " " for c in t).split() if w]
    if not words:
        return False
    alpha_n = sum(len(w) for w in words)
    if alpha_n < 4:
        return False
    # Real D2 names: one solid word (≥5, e.g. Shako) OR ≥2 words with a ≥4 letter piece
    # (Arachnid Mesh / Call to Arms). OCR crumbs like "ING THe R" fail this.
    long4 = sum(1 for w in words if len(w) >= 4)
    long5 = sum(1 for w in words if len(w) >= 5)
    if not (long5 >= 1 or (len(words) >= 2 and long4 >= 2) or (len(words) == 1 and len(words[0]) >= 5)):
        return False
    # reject all-caps single short fragments that are almost never full item names
    if len(words) == 1 and len(words[0]) <= 5 and words[0].isupper():
        return False
    # reject fragments with no real word shape (too few vowels relative to length)
    vowels = sum(1 for c in t if c.lower() in "aeiou")
    if vowels < 1 or (alpha_n >= 6 and vowels / alpha_n < 0.15):
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
    if t == "echo-sticky":
        return "same item still where it was this session (anchor/inventory/stash tab) — not re-counted as new"
    if t == "first-seen":
        return "first time this name was read this session"
    if t.startswith("moved:"):
        return "item location changed this session (" + t.split(":", 1)[1] + ") — re-reported"
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


_SKIP_AT = {}
def journal_skip(why, detail=""):
    """v880 (SIM spec A2.8) — negative events: the reel must show 'agent chose to wait' as a
    dim tick, not a 40s hole that reads as blindness. Throttled 5s per why."""
    try:
        now = time.time()
        if now - _SKIP_AT.get(why, 0.0) < 5.0:
            return
        _SKIP_AT[why] = now
        _journal({"ts": int(now * 1000), "kind": "skip", "lane": "skip", "why": str(why)[:40],
                  "note": str(detail)[:120], "sessionId": SESSION_ID, "n": 0})
    except Exception:
        pass


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
    # v946.1 — tab-strip OCR + sticky walk so gems/materials don't vanish into shared/empty
    _model_tab = _norm_stash_tab(rd.get("stashTab"), rd.get("scene"))
    _fp = frame_path_for_id(frame_id) if frame_id else ""
    _cap_for_tab = capture_ts or _capture_ts_from_frame_id(frame_id) or int(time.time() * 1000)
    stash_tab = _resolve_stash_tab(
        rd.get("scene"), rd.get("stashTab"),
        frame_path=_fp if (_fp and os.path.isfile(_fp)) else None,
        ocr_rd=ocr_rd, ts=_cap_for_tab)
    try:
        rd["stashTab"] = stash_tab  # lifecycle / state ring match journal
    except Exception:
        pass
    # v1522 — the live Chronicle visit. Recording is free; the READ is offered, never auto-fired.
    try:
        _closed_visit = _chron_visit_step(rd.get("scene"), rd.get("chronicleTab"),
                                          frame_id=frame_id, ts=_cap_for_tab)
        if _closed_visit and _closed_visit.get("n"):
            _lg = _closed_visit.get("ledger") or ""
            ev("read", "📜 Chronicle visit captured — %d frames%s · ask the console to read it"
               % (_closed_visit["n"], (" · " + ("Holy Grail" if _lg == "uniques" else "Set pieces"))
                  if _lg else " · ledger unread"))
            _journal({"lane": "chronicle", "kind": "visit", "ts": int(time.time() * 1000),
                     "ledger": _lg, "frames": _closed_visit["frames"][:120],
                     "n": _closed_visit["n"], "since": _closed_visit["since"],
                     "until": _closed_visit["until"]})
    except Exception:
        pass
    ocr_set = {_norm_name(x) for x in ((ocr_rd or {}).get("names") or [])}
    confirmed = [nm for nm in names if _norm_name(nm) in ocr_set]
    conf_note = ((" · ✓ocr " + ", ".join(confirmed[:3])) if confirmed else "")
    tab_note = (f" · tab:{stash_tab}" if stash_tab else "")
    if stash_tab and stash_tab != _model_tab:
        tab_note += "↻"  # tab identity refined (OCR/sticky) vs model alone
    # v948 — session sticky: split always-there Cube/Tomes/shared echoes from NEW/MOVED
    _now_sticky = int(time.time() * 1000)
    names_new, names_echo, names_moved, sticky_tags = _classify_name_sticky(
        names, rd.get("names_loc") or {}, stash_tab, rd.get("scene"), _now_sticky)
    # merge sticky tags into lifecycle (don't overwrite vault/throw verdicts)
    _lt = lc.get("lifecycle_tags") or {}
    for _nm, _tg in (sticky_tags or {}).items():
        if _nm not in _lt or _lt.get(_nm) in ("seen", "holding", ""):
            _lt[_nm] = _tg
    try:
        lc["lifecycle_tags"] = _lt
    except Exception:
        pass
    sticky_note = ""
    if names_new or names_moved:
        sticky_note = " · NEW " + ", ".join((names_new or names_moved)[:4])
        if names_echo:
            sticky_note += " · echo " + str(len(names_echo))
    elif names_echo and names:
        sticky_note = " · sticky echo ×" + str(len(names_echo)) + " (no new items)"
    # mind line prefers new/moved over cube spam
    _show = names_new if names_new else (names_moved if names_moved else names)
    line = ((("🗺 "+rd.get("area","")+" · ") if rd.get("area") else "") + tag + " " + str(rd.get("scene") or "")
            + tab_note + " — "
            + (", ".join(_show[:5]) + ("…" if len(_show) > 5 else "") if _show else "no readable item text (honest empty)")
            + sticky_note + lc_note + conf_note
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
        # v948 — session sticky split (full names kept for vision truth; new/echo for boards)
        "names_new": names_new,
        "names_echo": names_echo,
        "names_moved": names_moved,
        "sockets": rd.get("sockets") or {},        # v946.5 — per-item socket count (name -> N, 1..6)
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
        # v880 (SIM spec A2.5) — BOARD: what actually left the agent, per name. Verdict ≠
        # board effect; this is the effect, with 'nothing' names carrying their why.
        "board": {
            "vault": list(vault_names),
            "chronicle": sorted(set((rd.get("discovered") or [])
                                    + [n for n in names_new if (rd.get("names_loc") or {}).get(n) == "equipped"]
                                    + [n for n in names if (rd.get("names_loc") or {}).get(n) == "equipped"
                                       and n not in names_echo])),
            # v948 — only NEW/MOVED feed seen/chronicle boards; sticky echo stays off the noise path
            "seen": ([n for n in names_new if not _is_anchor(n) and not _is_junk(n)] if intent == "seen" else []),
            "unvault": list(unvault_names),
            "nothing": [{"name": n, "why": (lc.get("lifecycle_tags") or {}).get(n, "no-verdict")}
                        for n in names
                        if n not in vault_names and n not in (unvault_names or [])
                        and n not in names_echo
                        and not (intent == "seen" and not _is_anchor(n) and not _is_junk(n))],
            "echo": list(names_echo),
            "new": list(names_new),
            "moved": list(names_moved),
        },
        # v880 (SIM spec A2.6) — VISION: which image the model actually ate
        "vision": {
            "path": ("frames/hist/%s.jpg" % frame_id) if frame_id else "",
            "bytes": (os.path.getsize(os.path.join(HIST_DIR, str(frame_id) + ".jpg"))
                      if frame_id and os.path.isfile(os.path.join(HIST_DIR, str(frame_id) + ".jpg")) else 0),
            "timeoutMs": 75000,
            "escalated": bool(rd.get("escalated")),
            "finalModel": model_tag,
        },
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
    # v926 SECOND LOOK — queue a verify pass on any REAL item read (not sim/farewell/verify).
    # It runs in the next idle gap and corrects this exact frame's read.
    try:
        _itemish_names = [x for x in names if _itemish(x)]
        _fidk = str(frame_id)
        if (VERIFY_ON and _itemish_names and frame_id and not farewell
                and not rd.get("sim") and not _fidk.endswith("#v")
                and not any(j.get("fid") == _fidk for j in _VERIFY_Q)):   # fid-dedup: one look per frame
            if len(_VERIFY_Q) >= _VERIFY_Q.maxlen:
                try: ev("skip", "verify backlog full — dropped a second look")
                except Exception: pass
            _VERIFY_Q.append({"fid": _fidk, "names": _itemish_names, "vaulted": list(vault_names),
                              "n": n, "sid": SESSION_ID, "scene": rd.get("scene") or "loot", "cap_ms": _cap_ms})
    except Exception:
        pass
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
    """v847/v899 — seal the theatre reel then exit.
    Always journals session_end. Farewell vision is hard-capped (FAREWELL_MAX_S, default 12s)
    so End Session after a long run never sticks on SIGNING OFF for 90s+."""
    global _FAREWELL_DONE, _STOPPING
    if _FAREWELL_DONE:
        os._exit(0)
    _FAREWELL_DONE = True
    _STOPPING = True
    reason = str(reason or "stop")[:60]
    print(f"\n  👋 closing session ({reason})" + (" — farewell read…" if farewell else " — sealing reel…"))
    ev("boot", "session close · " + reason + (" · farewell" if farewell else " · soft off"))
    # v1689 — flush a Chronicle visit that is STILL OPEN. It goes BEFORE session_end so the visit
    # row lands inside the session it belongs to; without it, looking at the Chronicle last (the
    # natural way to register finds) journalled nothing at all. Free — no read is fired.
    try:
        chron_visit_flush()
    except Exception:
        pass
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
    # v925 LIGHT — the farewell VISION read is opt-in now (TV_FAREWELL=1). Default END SESSION
    # just seals + exits so it can NEVER hang on a Claude call (the "button stuck" bug).
    if farewell and not FAREWELL_READ_ON:
        farewell = False
        print("  👋 light end — sealed, no farewell read")
    try:
        # v925-R4 (Grok) — a light end must not join a stuck mid-flight read for 8s. Give the
        # pool ~2s to wind down; a full farewell run still gets the longer cap.
        # v1206 — keep_worker0 only when a real farewell read is actually about to run right
        # after this call; otherwise `_WORKER`'s warm claude -p child gets swept too instead of
        # orphaned (see _pool_shutdown's v1206 note).
        _pool_shutdown(timeout=(min(FAREWELL_MAX_S, 8.0) if farewell else 2.0), keep_worker0=farewell)
    except Exception:
        pass
    if farewell:
        # v899 — never block exit on a hung Claude farewell: race with hard deadline
        _fare_box = {"done": False}

        def _fare_run():
            try:
                with _emit_lock:
                    farewell_read()
            except Exception as e:
                print(f"  👋 farewell failed: {e}")
            finally:
                _fare_box["done"] = True

        _ft = threading.Thread(target=_fare_run, daemon=True, name="tv-farewell")
        _ft.start()
        _ft.join(timeout=FAREWELL_MAX_S)
        if not _fare_box["done"]:
            print(f"  👋 farewell timed out after {int(FAREWELL_MAX_S)}s — sealing without it")
            ev("skip", "farewell timed out · seal continues")
    _journal_flush(timeout=5.0)
    try:
        # v883 (Konyo: 'sessions are not showing the real frame-by-frame') — REEL FOLD: loose
        # f_*.jpg footage was a shared pool the reaper shed FIRST, so every sealed run went
        # hollow within hours. Fold this session's window into frames/hist/reel_<sid>/ —
        # rename on the same volume, instant — and the reaper retires whole old reels last.
        _hd = HIST_DIR
        _t0 = int(globals().get("_SESSION_T0_MS") or (SESSION_ID.split("_")[1] if "_" in SESSION_ID else 0) or 0)
        _t1 = int(time.time() * 1000) + 2000
        if os.path.isdir(_hd) and _t0:
            _reel = os.path.join(_hd, "reel_" + SESSION_ID)
            _moved = 0
            for _fn in os.listdir(_hd):
                if not (_fn.startswith("f_") and _fn.endswith(".jpg")):
                    continue
                try:
                    _fts = int(_fn[2:-4])
                except Exception:
                    continue
                if _t0 - 2000 <= _fts <= _t1:
                    if not _moved:
                        os.makedirs(_reel, exist_ok=True)
                    try:
                        os.replace(os.path.join(_hd, _fn), os.path.join(_reel, _fn))
                        _moved += 1
                    except Exception:
                        pass
            if _moved:
                # v894 — write reel index so SIM loads without scanning every jpg name
                #
                # v1608 (Konyo: 'still a black screen when trying to record') — THE INDEX *IS*
                # THE REEL, SO IT GOES DOWN FIRST. TWO PHASES. DO NOT RE-INVERT THEM.
                #
                # Measured on his real footage: chronicle_retro.is_dead_frame() costs ~0.076 s per
                # frame, so the blank pass below runs ~7.4 s on a 98-frame reel. Meanwhile
                # control_app.stop_agent() asks for shutdown (timeout 1.0 s), waits wait_s = 2.5 s
                # and then SIGKILLs every agent pid — the hard kill lands ~3.5 s after the ask.
                # Writing index.json only AFTER the blank pass therefore put the one artefact the
                # reel cannot exist without ~4 s the WRONG side of the kill: the 01:04 session
                # sealed 98 real jpgs and no index at all, and theatre / read_reel / sweep_hist all
                # read index.json — an index-less reel plays BLACK. The 1-frame reels survived only
                # because their pass finished in ~0.1 s. It is not deterministic (three older
                # 114/126/153-frame reels did get indexes; /api/off, window close and atexit give
                # different grace) — but the ordering is the whole difference:
                #   phase 1  filenames only, milliseconds, atomic  -> the reel is PLAYABLE
                #   phase 2  blank enrichment, time-boxed, atomic  -> the reel is nicer
                # The blank flags are an optimisation. The index is the reel's existence.
                _blank = 0
                _idx = []
                try:
                    _idx = sorted(
                        f for f in os.listdir(_reel)
                        if f.startswith("f_") and f.endswith(".jpg")
                    )
                except Exception as _e:
                    print(f"  ⛔ REEL LISTING FAILED for reel_{SESSION_ID}: {_e!r} — "
                          f"no index can be written, reel is UNPLAYABLE until repaired")

                def _reel_index_write(_doc):
                    # atomic: same-dir tmp -> flush -> fsync -> os.replace. A SIGKILL landing at any
                    # instant leaves either the previous index or the new one, never a half file.
                    _tmp = os.path.join(_reel, "index.json.tmp")
                    with open(_tmp, "w", encoding="utf-8") as _jf:
                        json.dump(_doc, _jf)
                        _jf.flush()
                        os.fsync(_jf.fileno())
                    os.replace(_tmp, os.path.join(_reel, "index.json"))

                # ── phase 1: filenames only ───────────────────────────────────────────────
                _meta = []
                for _fn in _idx:
                    try:
                        _meta.append({"f": _fn, "ts": int(_fn[2:-4])})
                    except Exception:
                        continue      # unparseable stamp is not a frame — same as v894
                _ixdoc = {"sessionId": SESSION_ID, "n": len(_meta),
                          "blank": 0, "frames": _meta, "blankPass": False}
                # v1595 — STAMP THE MINI. Without this the flag changes nothing that
                # outlives the process: vault_retro reads the sealed reel, not the argv of
                # a run that has already exited.
                if MINI_MODE:
                    _ixdoc["mini"] = True
                    _ixdoc["focus"] = MINI_FOCUS
                    # v1783 — RECORD WHETHER HE CHOSE THIS. The retro sweep skips the classifier
                    # for a declared focus on the v1603 premise that pressing MINI TELLS the app
                    # what he is parked on. That holds for a focus he picked and fails for one he
                    # never touched: "stash" is the default here, the console pre-selects it, and
                    # an untouched default then labels town, a fight and a Chronicle page as a
                    # stash panel without any of them being looked at. An untouched default is not
                    # a statement, so the sweep is told which kind of stamp this is.
                    _ixdoc["focusChosen"] = MINI_FOCUS_CHOSEN
                    _ixdoc["miniSeconds"] = MINI_SECONDS
                _indexed = False
                for _attempt in (1, 2):     # one retry, then say so out loud
                    try:
                        _reel_index_write(_ixdoc)
                        _indexed = True
                        break
                    except Exception as _e:
                        if _attempt == 2:
                            print(f"  ⛔ REEL INDEX WRITE FAILED for reel_{SESSION_ID}: {_e!r} — "
                                  f"reel is UNPLAYABLE until repaired")
                if _indexed:
                    print(f"  🗂 reel index written — reel_{SESSION_ID} lists "
                          f"{len(_meta)} frame(s)")

                # ── phase 2: blank enrichment ─────────────────────────────────────────────
                # v1545 — MARK THE BLANK CAPTURES, ONCE, HERE.
                #
                # 18 of the 394 frames in his sealed footage are the window grabbed with nothing
                # on it, and 16 of the 17 in the worst reel land in the FIRST NINETEEN SECONDS:
                # capture starts while D2R is still launching, so the window exists (the grab
                # succeeds) and is blank until the title screen paints.
                #
                # Marking beats deleting — that footage is real, the SIM replays it, and throwing
                # away evidence to tidy a count is the wrong trade. Marking beats measuring later
                # too: the flatness is computed once at seal instead of on every sweep, and a
                # blank frame sitting inside a real Chronicle visit no longer splits that visit
                # into two runs and charges for two classifies.
                #
                # v1608 — and TIME-BOXED at 2.0 s, under the console's 2.5 s force-kill. Unbounded,
                # this pass is guaranteed to be killed on any real reel; whatever it cannot reach
                # in time simply stays unmarked (blankPartial), which is honest, and the phase-1
                # index is already on disk so the reel plays either way.
                if _indexed and _meta:
                    _t_blank = time.time()
                    _scanned = 0
                    _partial = False
                    try:
                        import chronicle_retro as _cr
                        for _row in _meta:
                            if time.time() - _t_blank > 2.0:
                                _partial = True
                                break
                            try:
                                if _cr.is_dead_frame(os.path.join(_reel, _row["f"])):
                                    _row["blank"] = True
                                    _blank += 1
                            except Exception:
                                pass      # unmeasurable stays unmarked — never guessed blank
                            _scanned += 1
                        _ixdoc["blank"] = _blank
                        _ixdoc["blankPass"] = True
                        if _partial:
                            _ixdoc["blankPartial"] = True
                            _ixdoc["blankScanned"] = _scanned
                        _reel_index_write(_ixdoc)
                    except Exception as _e:
                        print(f"  ⚠ reel_{SESSION_ID}: blank-capture pass incomplete ({_e!r}) — "
                              f"index stands, those frames are just unmarked")
                print(f"  🎞 reel folded — {_moved} footage frames sealed into reel_{SESSION_ID}")
                # v1548 — the warm-up gate is only trustworthy if it says what it withheld
                _ws = int(globals().get("_FOOTAGE_WARMSKIP") or 0)
                if _ws:
                    print(f"  ⏳ {_ws} frame(s) held back while D2R was still painting — "
                          f"blank captures that never reached the reel")
                # ── v1608.1 — THE LATE SWEEP. Phase 2 runs up to 2 s AFTER the fold above, and the
                # film thread keeps writing f_<ms>.jpg into FRAMES the whole time. Those frames land
                # after the fold has already walked the directory, so they stay loose — outside the
                # reel, in the shared pool the reaper sheds FIRST (the exact v883 bug: sessions going
                # hollow within hours). test_roundtrip_sim caught it as "loose frames survived the
                # fold inside the session window", which is footage he would simply never see again.
                #
                # So sweep once more, with the SAME window rule as the fold, and re-index if anything
                # moved. Cheap (one listdir, a rename each) and it closes the window no matter how
                # long phase 2 took — which matters because phase 2's duration is deliberately
                # variable.
                try:
                    _late = 0
                    _t1b = int(time.time() * 1000) + 2000
                    for _fn in os.listdir(_hd):
                        if not (_fn.startswith("f_") and _fn.endswith(".jpg")):
                            continue
                        try:
                            _fts = int(_fn[2:-4])
                        except Exception:
                            continue
                        if _t0 - 2000 <= _fts <= _t1b:
                            try:
                                os.replace(os.path.join(_hd, _fn), os.path.join(_reel, _fn))
                                _late += 1
                                _meta.append({"f": _fn, "ts": _fts})
                            except Exception:
                                pass
                    if _late:
                        _meta.sort(key=lambda _r: _r["ts"])
                        _ixdoc["frames"] = _meta
                        _ixdoc["n"] = len(_meta)
                        _ixdoc["lateFolded"] = _late
                        _reel_index_write(_ixdoc)
                        print(f"  🧹 {_late} late frame(s) folded in after the seal pass")
                except Exception as _e:
                    print(f"  ⚠ late fold sweep skipped ({_e!r}) — some frames may remain loose")

                # said out loud, because a capture lane producing blank frames is a fault that would
                # eat a real Chronicle page exactly as happily as it eats a loading screen
                if _blank:
                    print(f"  ⚠ {_blank} blank capture(s) in this reel — the window was grabbed with "
                          f"nothing painted on it (usually D2R still launching)")
    except Exception as _e:
        # v1608 — a reel fold that dies silently is how footage disappears without a trace
        print(f"  ⛔ REEL FOLD FAILED for reel_{SESSION_ID}: {_e!r} — "
              f"this session's footage may be unsealed or unindexed")
    with _state_lock:
        try:
            st = _load()
            st["online"] = False
            st["stopping"] = False
            st["sessionId"] = SESSION_ID
            _save(st)
            _state_flush()   # v879 — Grok flush list #3/#6: never exit with a dirty write-behind
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
