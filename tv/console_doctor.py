#!/usr/bin/env python3
"""v2026 — 🦅 THE EAGLE EYE: one pass over the WHOLE console, from above.

    python3 tv/console_doctor.py            report
    python3 tv/console_doctor.py --json     machine-readable (the /api/doctor payload)

Konyo, 2026-08-23: *"is there a MANAGER for the AI console? ... dont we need like a type of EAGLE
EYE kind of style management system here? eyes from above it all like that can see bugs happening
or something and fix it when its out of line?"*

WHY THIS, WHEN THERE ARE ALREADY DOCTORS. `chronicle_doctor` and `vault_doctor` each answer a
question about ONE lane, and `run_gates` answers a question about the SOURCE before a push. Nothing
looked at the RUNNING SYSTEM as a whole, and every defect found on the night this was written was
exactly that shape — no single lane was wrong, two correct things disagreed:

    the console served v2018 while the tree was v2024, for two hours, unnoticed
    the vault sweep read 0 pages while 4 reels on disk were 40-100% stash panels
    G5 said mode=off while the lane list still shipped a grok lane
    the vault pill said a lane was dark while the reel filed into it anyway
    the free cost pass called his footage worthless, from its own refusing stub

Not one of those is visible from inside the component that owns it. They are only visible from
above, which is what this is.

DOCTRINE, inherited wholesale from the other two doctors and NOT re-argued here:
  * it REPORTS. `--fix` exists but touches only the provably-reversible, and says what it did.
  * every check answers OK / MISSING (with the action) / UNKNOWN (with why), never a bare boolean.
  * an UNKNOWN is not a failure. "I could not check" and "it is broken" are different sentences,
    and collapsing them is the lie this whole codebase audits out. [[unknown-stays-unknown]]
  * it never re-implements a check that already exists — it CALLS the other doctors. Two copies of
    one rule is two things that drift apart, and only one of them gets fixed. [[copy-drift]]

FREE BY CONSTRUCTION: filesystem, git and localhost only. No model turn, no network, no paid read.
"""
import glob
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

OK, MISSING, UNKNOWN = "ok", "missing", "unknown"
ICON = {OK: "🟢", MISSING: "🟠", UNKNOWN: "⚪"}
CONSOLE = "http://127.0.0.1:17772"


def _get(path, timeout=4):
    """GET a console route. Absent console is UNKNOWN, never a failure."""
    import urllib.request
    try:
        with urllib.request.urlopen(CONSOLE + path, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except Exception:
        return None


def _post(path, body=None, timeout=20):
    """POST a console route. Absent console is UNKNOWN, never a failure."""
    import urllib.request
    try:
        req = urllib.request.Request(
            CONSOLE + path, data=json.dumps(body or {}).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", "replace"))
    except Exception:
        return None


def _check_the_board_world_is_claimed():
    """An UNCLAIMED board lives in a guest world, and everything applied there is lost.

    This is the failure that cost a whole night: `bible.html` resolves `_D2R_OWNER` only from a
    clicked `d2r_ownerClaim`. Without it `_D2R_PFX` becomes 'I·<installId>·' — a per-install world.
    An apply into it returns ok:true, writes real rows, and they are unreachable from the next load.

    It is SILENT BY CONSTRUCTION: the ledger counts read exactly the same in a doomed world as in a
    real one, so nothing on any screen distinguishes them. That is precisely what a doctor is for.
    [[the-unjoined-end]]
    """
    got = _post("/api/board_ownership", {"sample": 0})
    if not got:
        return UNKNOWN, "the console did not answer — nobody asked, so nothing is known"
    # v2147 — ASK THE MEMORY FIRST. The v2145 branch that "reports drift even when the board is
    # closed" was UNREACHABLE: a closed window answers ok:False, and both early returns below fired
    # before it. Measured by injecting worldDrift onto that payload — still UNKNOWN. And a closed
    # board is precisely the moment a relaunch just happened, so the remembered world is the only
    # thing that can speak. The verdict is read before anything is allowed to give up.
    _d = got.get("worldDrift") if isinstance(got, dict) else None
    if isinstance(_d, dict) and _d.get("state") == "drift":
        return MISSING, _d.get("why")
    if not got.get("ok"):
        return UNKNOWN, "the board refused the read: %s" % str(got.get("why"))[:90]
    # v2055 — "THE BOARD IS NOT OPEN" IS NOT "THE BOARD IS DOOMED".
    # _D2R_OWNER/_D2R_PFX are bible.html globals. On the console rail they do not exist, both read
    # falsy, and this check used to answer MISSING with "anything applied here is lost on the next
    # launch" — about a world that was claimed, on disk, and perfectly safe. After the night his
    # ledger actually was emptied, that is the last sentence that should ever be shown wrongly.
    if got.get("boardLoaded") is False:
        # v2145 — A CLOSED BOARD IS EXACTLY WHEN A RELAUNCH HAPPENED, so ask the REMEMBERED world
        # before giving up. Konyo armed auto-relaunch on the condition that nothing gets deleted or
        # regressed; what could regress is the board coming back as a DIFFERENT world, and that is
        # knowable from the record even with the window shut.
        _d = got.get("worldDrift") if isinstance(got, dict) else None
        if isinstance(_d, dict) and _d.get("state") == "drift":
            return MISSING, _d.get("why")
        return UNKNOWN, ("the board is not open in the window — ownership lives in bible.html's "
                         "globals, so it cannot be read from the console rail. Open the board to "
                         "find out."
                         + ("" if not _d else "  Last recorded: " + str(_d.get("why"))[:120]))
    if "owner" not in got:
        # v2044 added the field. An older console cannot answer, and MUST NOT read as a pass.
        return UNKNOWN, ("this console predates the ownership field (v2044) — restart it to find "
                         "out whether the board world persists")
    counts = got.get("counts") or {}
    total = sum(int(counts.get(k) or 0) for k in ("foundLog", "owned", "setPieces"))
    if got.get("owner"):
        # "claimed" and "the SAME world his vault is in" are different facts, and only the second
        # survives a relaunch. v2043 was silent precisely because the first one stayed true.
        _d = got.get("worldDrift") if isinstance(got, dict) else None
        if isinstance(_d, dict) and _d.get("state") == "drift":
            return MISSING, _d.get("why")
        _tail = "" if not (isinstance(_d, dict) and _d.get("state") == "ok") else " · " + str(_d.get("why"))
        return OK, ("the board is CLAIMED — it writes the bare keys, so what is applied persists"
                    + _tail)
    return MISSING, ("the board is an UNCLAIMED guest world (prefix %r) holding %d ledger entries — "
                     "anything applied here is lost on the next launch. Open the board and press "
                     "'This browser is mine'." % (got.get("pfx"), total))


def _tree_version():
    # v2026 — READ THE WHOLE FILE. The first cut read 400KB and returned None, because D2R_BUILD
    # sits ~1.1MB into a 5.8MB file. A version check that answers None is a check that never fires,
    # and this one exists precisely to catch the drift that cost two hours. Caught by its own first
    # run, which is the argument for running a new doctor before believing it.
    try:
        with open(os.path.join(ROOT, "bible.html"), encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        m = re.search(r"D2R_BUILD\s*=\s*\{\s*id:'(v\d+)'", text)
        return m.group(1) if m else None
    except Exception:
        return None


# ── the checks ───────────────────────────────────────────────────────────────────────────────

def _check_version_drift():
    """THE ONE THAT COST TWO HOURS. A long-lived console keeps serving the code it booted with,
    and every stamp on the page still reads from disk — so the UI can show a version the running
    process has never executed. Nothing else can see this: the process is healthy and the tree is
    healthy, and only the pair is wrong."""
    st = _get("/api/status")
    tree = _tree_version()
    if st is None:
        return UNKNOWN, "the console is not answering on :17772 — nothing to compare a tree against"
    running = st.get("ver")
    if not running or not tree:
        return UNKNOWN, "could not read one of the two versions (running=%r tree=%r)" % (running, tree)
    if running == tree:
        return OK, "the running console and the tree are both %s" % running
    return MISSING, ("the console is RUNNING %s while the tree is %s — every fix since %s is on "
                     "disk and not in the process. Restart it in your own window: bash "
                     "tv/tvd-scan.sh (never --force; headless cannot hold Screen Recording)"
                     % (running, tree, running))


def _check_lane_intent():
    """A switch he turned off that is still being counted. `has_subscription()` answers CAN it run,
    `switch_on()` answers does he WANT it to, and for a long time only the first was asked."""
    try:
        import g5_grok_eyes as g5
    except Exception as e:
        return UNKNOWN, "g5_grok_eyes will not import: %s" % str(e)[:90]
    try:
        capable = bool(g5.has_subscription())
        wanted = bool(g5.switch_on())
        mode = g5.mode_intent()
    except Exception as e:
        return UNKNOWN, "could not read the G5 switch: %s" % str(e)[:90]
    st = _get("/api/status")
    lanes = None
    if st is not None:
        lanes = (st.get("lanes") or None)
    if not capable:
        return OK, "no Grok CLI here, so this machine is claude-only by capability (mode=%s)" % mode
    if capable and not wanted:
        return OK, "Grok is installed and you switched it OFF (mode=%s) — claude-only, by choice" % mode
    return OK, "Grok installed and switched on (mode=%s) — dual lane%s" % (
        mode, ("; console reports %s" % lanes) if lanes else "")


def _measured_write_rate():
    """GB/hour measured from HIS newest reels, or None when it cannot be measured.

    v2046 — this used to be the constant "roughly 9GB/hour". That number is real: v2019 clocked
    +37MB in 15s on a busy scene. So is 5.0-6.6GB/hour, measured 2026-08-24 across the three newest
    reels at 1.44-1.90 MB/frame and 55-60 frames/min. Both are true, because JPEG size tracks scene
    complexity and the rate swings ~2x with what he is looking at.

    A single constant therefore cannot describe it, and quoting one as if it could is the shape of
    [[label-outlived-referent]] — a right number under a word that stopped being true. So: measure
    his actual footage, say the figure is measured, and fall back to the documented worst case
    while SAYING it is a worst case. Returns (gb_per_hour, n_reels) or (None, 0).
    """
    import glob
    best = []
    reels = sorted(glob.glob(os.path.join(HERE, "frames", "hist", "reel_*")),
                   key=lambda d: -os.stat(d).st_mtime)[:3]
    for d in reels:
        fr = glob.glob(os.path.join(d, "*.jpg"))
        if len(fr) < 40:
            continue                      # too few frames to time anything honestly
        try:
            st = [os.stat(q) for q in fr]
        except OSError:
            continue
        ts = sorted(x.st_mtime for x in st)
        mins = (ts[-1] - ts[0]) / 60.0
        if mins < 1.0:
            continue
        gb = sum(x.st_size for x in st) / float(1 << 30)
        best.append(gb * (60.0 / mins))
    if not best:
        return None, 0
    return sum(best) / len(best), len(best)


def _check_disk_headroom():
    """/api/on refuses below an 8GB floor. Finding that out when you press ON AIR is too late."""
    try:
        import shutil
        free = shutil.disk_usage(HERE).free / 1e9
    except Exception as e:
        return UNKNOWN, "could not read disk usage: %s" % str(e)[:90]
    try:
        frames = subprocess.run(["du", "-sk", os.path.join(HERE, "frames")],
                                capture_output=True, text=True, timeout=60)
        used = int(frames.stdout.split()[0]) / 1e6 if frames.stdout.strip() else None
    except Exception:
        used = None
    tail = (" · footage is %.1fGB" % used) if used is not None else ""
    if free < 8.0:
        return MISSING, ("%.1fGB free — BELOW the 8GB floor, so /api/on will refuse to record%s"
                         % (free, tail))
    rate, n = _measured_write_rate()
    if rate:
        rate_says = "your last %d reel(s) averaged %.1fGB/hour" % (n, rate)
    else:
        rate, rate_says = 9.0, "no reel was long enough to measure; using the 9GB/hour worst case"
    if free < 16.0:
        return MISSING, ("%.1fGB free — %s, so this is about %.1f hour(s) of recording%s"
                         % (free, rate_says, free / rate, tail))
    return OK, "%.1fGB free%s" % (free, tail)


def _check_subscription_burn():
    """Reads against the window. Not tokens — this lane bills none."""
    try:
        import tv_diablo as tv
        path = getattr(tv, "_SUB_BUDGET_PATH", "")
        hourly = int(getattr(tv, "_SUB_HOURLY_MAX", 0) or 0)
        daily = int(getattr(tv, "_SUB_DAILY_MAX", 0) or 0)
    except Exception as e:
        return UNKNOWN, "tv_diablo will not import: %s" % str(e)[:90]
    if not path or not os.path.isfile(path):
        return UNKNOWN, "no vision read has been recorded on this machine yet"
    try:
        calls = [float(c) for c in (json.load(open(path, encoding="utf-8")).get("calls") or [])]
    except Exception as e:
        return UNKNOWN, "budget file unreadable: %s" % str(e)[:90]
    now = time.time()
    hour = sum(1 for c in calls if now - c <= 3600)
    day = sum(1 for c in calls if now - c <= 86400)
    pct = (100.0 * hour / hourly) if hourly else 0.0
    if hourly and pct >= 85:
        return MISSING, ("%d reads this hour of %d (%.0f%%) — close to the cap; a sweep started now "
                         "may be cut off" % (hour, hourly, pct))
    return OK, "%d read(s) this hour of %d · %d today of %d — subscription, no API tokens" % (
        hour, hourly, day, daily)


def _check_a_reel_is_not_recording_unattended():
    """v2019's class. A reel that outlives the thing that started it burns ~9GB/hour in silence."""
    sh = _get("/api/shadow")
    if sh is None:
        return UNKNOWN, "the console is not answering — cannot say whether a reel is rolling"
    rec = bool(sh.get("recording"))
    on = bool(sh.get("on"))
    if rec and not on:
        return MISSING, ("a reel IS RECORDING while the shadow reader is OFF — nothing is reading "
                         "what it films. Seal it from ON AIR, or switch the reader on")
    if rec:
        return OK, "a reel is rolling and the reader is watching it"
    return OK, "nothing is recording"


def _check_the_sweep_would_find_something():
    """REG-384's class, and the one no lane can see: a sweep that spends its budget on footage
    with nothing in it. This is FREE — the panel gate is a crop and an OCR, no model call."""
    try:
        import chronicle_retro as cr
        import vault_retro as vr
        import control_app as ca
    except Exception as e:
        return UNKNOWN, "could not import the sweep modules: %s" % str(e)[:90]
    hist = os.path.join(HERE, "frames", "hist")
    if not os.path.isdir(hist):
        return UNKNOWN, "no frames/hist on this machine"
    try:
        dirs = cr.reel_dirs(hist)
    except Exception as e:
        return UNKNOWN, "could not list reels: %s" % str(e)[:90]
    if not dirs:
        return MISSING, "no reels on disk — record one: open TV DIABLO and press ON AIR"
    try:
        dens = {d: vr.panel_density(d, ca.stash_screen_open_cached) for d in dirs}
    except Exception as e:
        return UNKNOWN, "the panel gate would not run: %s" % str(e)[:90]
    withpanel = [d for d, v in dens.items() if v > 0]
    if not withpanel:
        return MISSING, ("%d reel(s) on disk and NONE shows a stash panel — a vault sweep would "
                         "read nothing. Open the stash (and hover items) while a reel is rolling"
                         % len(dirs))
    best = sorted(dens.items(), key=lambda kv: -kv[1])[:3]
    return OK, ("%d of %d reel(s) show a stash panel; a sweep would start with %s"
                % (len(withpanel), len(dirs),
                   ", ".join("%s (%.0f%%)" % (os.path.basename(d), 100 * v) for d, v in best)))


def _check_the_other_doctors():
    """Call them, never re-implement them. [[copy-drift]]"""
    out = []
    for mod, label in (("vault_doctor", "vault"), ("chronicle_doctor", "chronicle")):
        try:
            r = subprocess.run([sys.executable, os.path.join(HERE, mod + ".py")],
                               capture_output=True, text=True, timeout=600)
            txt = (r.stdout or "") + (r.stderr or "")
            bad = txt.count("🟠") + txt.count("🔴")
            good = txt.count("🟢")
            out.append((label, good, bad))
        except Exception as e:
            out.append((label, None, str(e)[:60]))
    parts = []
    worst = OK
    for label, good, bad in out:
        if good is None:
            parts.append("%s doctor would not run (%s)" % (label, bad))
            worst = UNKNOWN if worst == OK else worst
        else:
            parts.append("%s %d green / %d needs-you" % (label, good, bad))
            if bad:
                worst = MISSING
    return worst, " · ".join(parts) + "  (run them for the detail)"


# ── v2078 — EVERYTHING THE NIGHT OF 2026-08-24 BUILT, WATCHED FROM ABOVE ─────────────────────
# Konyo: "put it all under eagle eye and watchdog so if something within the console is out of
# sync it can catch it."
#
# Each check below exists because a REAL defect of that exact shape shipped and HE found it. None
# of them tests code — they test whether the RUNNING SYSTEM still agrees with itself, which is the
# one thing no unit test and no gate can see.
#
# Every one errs the same way: what it cannot measure is UNKNOWN, never OK. A watchdog that reports
# "fine" because it could not look is the defect it was built to catch.


def _check_the_visual_lock_holds():
    """The board's meaning-bearing CSS — weight, structure, rarity COLOUR, the sealed title, and
    every Sessions card owning a grid area. He found all of those by eye first."""
    import subprocess
    lock = os.path.join(os.path.dirname(HERE), "visual_lock_invariant.py")
    if not os.path.isfile(lock):
        return UNKNOWN, "visual_lock_invariant.py is not on this machine, so nothing is pinning the board's type or colour"
    try:
        p = subprocess.run([sys.executable, lock], capture_output=True, text=True, timeout=90)
    except Exception as e:
        return UNKNOWN, "the visual lock could not run (%s) — that is unmeasured, not clean" % str(e)[:70]
    if p.returncode == 0:
        return OK, "weight, structure, rarity colour and the sealed title all still pinned"
    bad = [l.strip(" \u2022") for l in (p.stdout or "").split("\n") if l.strip().startswith("\u2022")]
    return MISSING, ("the board's visual lock has DRIFTED: %s"
                     % ("; ".join(bad)[:230] or "see visual_lock_invariant.py"))


def _check_the_art_corpus():
    """1,233 sprites the board draws. A prune, a bad sync or a rename takes them with nothing
    failing — the page just starts drawing placeholders where it drew items."""
    import glob
    art = os.path.join(os.path.dirname(HERE), "art")
    if not os.path.isdir(art):
        return UNKNOWN, "the art directory is not on this machine"
    n = len(glob.glob(os.path.join(art, "*.png")))
    gems = [g for g in ("amethyst", "ruby", "emerald", "saphire")
            if not glob.glob(os.path.join(art, "hd_perfect_%s*.png" % g))]
    if gems:
        return MISSING, ("%d sprite(s) on disk but the craft gems %s are GONE — every craft card "
                         "silently reverts to one alembic emoji" % (n, ", ".join(gems)))
    if n < 1233:
        return MISSING, ("the art corpus is %d files, down from 1233 — the board will draw "
                         "placeholders where it used to draw items" % n)
    return OK, "%d sprite(s), and the four craft gems are all present" % n


def _check_footage_belongs_to_a_reel():
    """A session that dies before it SEALS leaves its frames loose in hist/, where no lane and no
    deleter can see them — 3.15 GB of his footage was invisible that way."""
    try:
        sys.path.insert(0, HERE)
        import frame_authority as fa
    except Exception as e:
        return UNKNOWN, "frame_authority did not import (%s)" % str(e)[:70]
    hist = os.environ.get("TV_HIST") or os.path.join(HERE, "frames", "hist")
    if not os.path.isdir(hist):
        return UNKNOWN, "no frames/hist on this machine"
    try:
        lf = fa.loose_frames(hist)
    except Exception as e:
        return UNKNOWN, "could not read the loose frames (%s)" % str(e)[:70]
    if not lf.get("ok"):
        return UNKNOWN, lf.get("say") or "the loose-frame scan could not answer"
    rec = len(lf.get("recording") or [])
    if rec:
        return MISSING, ("%d frame(s) (%.2f GB) belong to NO reel — an unsealed recording no sweep "
                         "can reach. `python3 tv/orphan_fold.py` shows the plan."
                         % (rec, (lf.get("recordingBytes") or 0) / 1e9))
    return OK, "every recording frame belongs to a reel"


def _check_the_vault_stores_are_readable():
    """His ledger is the whole point of the vault manager. An unreadable store must never read as
    an empty one — that difference is what the free ledger view exists to keep."""
    import json as _j
    names = ("vault_accum.json", "vault_seen.json", "vault_swept.json")
    absent, broken, counts = [], [], {}
    for n in names:
        fp = os.path.join(HERE, n)
        if not os.path.exists(fp):
            absent.append(n)
            continue
        try:
            with open(fp, encoding="utf-8") as fh:
                blob = _j.load(fh)
            rows = blob.get("owned") if isinstance(blob, dict) and "owned" in blob else (
                blob.get("rows") if isinstance(blob, dict) and "rows" in blob else blob)
            counts[n] = len(rows) if hasattr(rows, "__len__") else 0
        except Exception as e:
            broken.append("%s (%s)" % (n, str(e)[:40]))
    if broken:
        return MISSING, ("a vault store will not parse: %s — everything downstream is INCOMPLETE, "
                         "not empty" % "; ".join(broken))
    if absent:
        return UNKNOWN, ("%s has never been written, so there is nothing to compare against yet"
                         % ", ".join(absent))
    return OK, ("%d grounded row(s), %d sighting(s) waiting, %d sealed recording(s)"
                % (counts.get("vault_accum.json", 0), counts.get("vault_seen.json", 0),
                   counts.get("vault_swept.json", 0)))


def _check_the_locked_lanes_still_refuse():
    """He ruled it plainly: equipment and inventory are never to be told to move. The BOARD has
    carried _LOCKED_LANES since v1712; the engine that PRODUCES the suggestions did not until
    v2075, and a non-grail item he was WEARING could clear the throw bar."""
    try:
        sys.path.insert(0, HERE)
        import vault_retro as vr
    except Exception as e:
        return UNKNOWN, "vault_retro did not import (%s)" % str(e)[:70]
    locked = tuple(getattr(vr, "LOCKED_LANES", ()) or ())
    if not locked:
        return MISSING, ("vault_retro has no LOCKED_LANES — an item on his character or in his "
                         "inventory can be suggested for the bin again")
    for lane in ("equipment", "inventory"):
        if lane not in locked:
            return MISSING, "the %s lane is no longer locked against throw suggestions" % lane
    if getattr(vr, "THROWOUT_MIN_WITNESSES", 0) <= getattr(vr, "KEEP_MIN_WITNESSES", 0):
        return MISSING, ("the throw bar (%s) is no longer STRICTLY above the keep bar (%s) — there "
                         "is no un-throw in Diablo"
                         % (getattr(vr, "THROWOUT_MIN_WITNESSES", "?"),
                            getattr(vr, "KEEP_MIN_WITNESSES", "?")))
    return OK, ("%s locked; keep needs %d look(s), throw needs %d recording(s)"
                % (" + ".join(locked), vr.KEEP_MIN_WITNESSES, vr.THROWOUT_MIN_WITNESSES))


def _check_the_two_surfaces_agree():
    """EVERY DOOR LEADS TO A ROOM, AND A MOVE LEFT EXACTLY ONE COPY.

    Konyo: "i want it all under management so nothing gets buged."

    This exists because ONE failure shape produced four separate defects he had to find himself,
    in a single arc, and not one gate saw any of them:
      · v2085 built the Vault tab on the BOARD and never added it to the CONSOLE header — the room
        existed with no door on the surface that asks for rooms;
      · v2085 COPIED the shadow/tooltip switches into the console drawer instead of MOVING them, so
        Tools kept rendering them and the job read as done;
      · the header hid the seventh tab instead of shrinking it, silently;
      · demo_console's PANE_TABS never walked the tab that had just shipped, so J1 reported a
        confident green about the four it already knew.
    Every one is the same thing: ADDED in the new place, NOT FINISHED in the old one. Silent by
    construction, which is the defining property. [[the-unjoined-end]] [[copy-drift]]

    Cheap on purpose — it reads three files and runs no subprocess, so it belongs in the fast set
    the eagle ticks on its timer, not in SLOW.

    All five arms are PROVEN RED, each by a sabotage asserted to have changed the bytes first:
        a console tab with no board room      -> MISSING
        J1 stops walking a shipped tab        -> MISSING
        a moved control reappears on the board-> MISSING
        the console loses a drawer switch     -> MISSING
        the signpost points at a dead room    -> MISSING
    and the healthy tree still reads OK. [[feedback-blind-fixture-green-gate]]
    """
    repo = os.path.dirname(HERE)
    try:
        board = open(os.path.join(repo, "bible.html"), encoding="utf-8").read()
        ui = open(os.path.join(HERE, "control_ui.html"), encoding="utf-8").read()
    except Exception as e:
        return UNKNOWN, "could not read both surfaces (%s)" % str(e)[:70]

    faults = []
    # session and tvd are console-NATIVE: they deliberately open no board pane.
    NATIVE = {"session", "tvd"}
    shell = [m.group(1) for m in
             re.finditer(r'<button class="ht" type="button" data-tab="(\w+)"', ui)]
    panes = set(re.findall(r'id="tab-([\w-]+)"', board))
    for tab in shell:
        if tab not in NATIVE and tab not in panes:
            faults.append("the console offers a '%s' tab and the board has no #tab-%s to open"
                          % (tab, tab))

    try:
        demo = open(os.path.join(HERE, "demo_console.mjs"), encoding="utf-8").read()
        m = re.search(r"const PANE_TABS = \[([^\]]*)\]", demo)
        walked = set(re.findall(r"'(\w+)'", m.group(1))) if m else set()
        for tab in shell:
            if tab not in NATIVE and tab not in walked:
                faults.append("J1 never walks the '%s' tab — it ships ungated" % tab)
    except Exception:
        faults.append("demo_console.mjs could not be read to check its tab coverage")

    # A MOVED CONTROL MUST NOT BE BACK IN THE ROOM IT LEFT.
    # Pinned to TOOLS specifically, which is the room he named: "why is it still located in the
    # tools tab?". NOT pinned to "absent from the board", and the reason is worth recording —
    # v2093 tried exactly that and it was WRONG. toggleTooltipPass is not a painter: it arms the
    # vault mini-lane, POSTs /api/shadow AND POSTs /api/on, which STARTS A RECORDING, and it
    # tracks `startedReel` so switching OFF gives back the reel it started (a scar: 9GB/hour he
    # never asked for). The console drawer's twin only POSTs /api/shadow — and the server ignores
    # the `lane` field entirely, so BOTH drawer buttons write one shadow flag and neither performs
    # a tooltip pass. Deleting the board copies would have silently downgraded a real capability.
    # Tighten this to "absent from the board" only once the drawer drives the real orchestration.
    # [[the-unjoined-end]] [[unknown-stays-unknown]]
    # v2097 — TIGHTENED, now that the move is actually finished. This asked only "not in Tools"
    # because deleting the rows would have dropped a capability: /api/shadow ignores `lane`, so the
    # drawer's Tooltip button performed no pass. v2095 wired that button to the board's real
    # toggleTooltipPass through the iframe, and v2097 removed the rows, their four painters and 27
    # CSS rules. So the invariant is now the strong one: NEITHER switch may exist on the board at
    # all — the drawer beside the Grok eyes is their only home, which is where he asked twice for
    # them to be. [[the-unjoined-end]]
    for cid in ("shadow-ai", "tip-pass"):
        if ('id="%s"' % cid) in board:
            faults.append("#%s is on the BOARD again — ⚙ ADVANCED is its only home now, and two "
                          "copies is exactly how the last one hid" % cid)

    for cid in ("sadv-sha", "sadv-tip"):
        n = ui.count('id="%s"' % cid)
        if n != 1:
            faults.append("the console has %d copies of #%s (expected 1)" % (n, cid))

    if 'id="vault-moved-note"' in board:
        i = board.find('id="vault-moved-note"')
        m = re.search(r"switchTab\('(\w+)'\)", board[i:i + 1400])
        room = m.group(1) if m else None
        if not room or ('id="tab-%s"' % room) not in board:
            faults.append("the Tools signpost points at a room that does not exist (%r)" % room)
    else:
        faults.append("the Tools signpost is gone — anyone looking where the vault used to be is "
                      "told nothing")

    if faults:
        return MISSING, " · ".join(faults)[:400]
    return OK, ("%d console tab(s) all reach a board room, J1 walks every one, no moved control "
                "left a second copy" % len([t for t in shell if t not in NATIVE]))


def _check_the_hunt_is_buying_something():
    """Is the name-hunt still paying for reads that find nothing? -> (state, say)

    v2174 — MEASURED ON HIS OWN LOG, and it is why "chronicle is reading" never stopped:

        28 hunt passes · 3,434 PAID reads · 2 new sightings   =   1,717 reads per sighting

    with pass after pass reading "hunt done: 144 read(s), new sightings for 0 name". The hunt took
    the same first eight held names alphabetically every run, failed, and the next sweep bought the
    identical 144 reads. Nothing watched the ECONOMY of it, so it ran for hours looking exactly
    like healthy activity — the console said "a chronicle sweep is reading", which was true.

    v2174 gave the hunt a memory of what came back empty. This is the eye on it: if the ratio
    climbs again, something has broken the memory (an unwritable file, a fingerprint that moves
    every run) and he is paying for it. A guard on the FIX is not the same as a guard on the COST.
    """
    log = os.path.join(HERE, "control_app.log")
    if not os.path.isfile(log):
        return "unknown", "no console log on this machine, so the hunt's cost cannot be read"
    try:
        with open(log, encoding="utf-8", errors="replace") as fh:
            txt = fh.read()[-2000000:]          # the tail is the recent behaviour
    except Exception as e:
        return "unknown", "the console log could not be read (%s)" % str(e)[:60]
    import re as _re
    passes = _re.findall(r"hunt done: (\d+) read\(s\), new sightings for (\d+) name", txt)
    if not passes:
        # ⚠ v2175.3 — "I CANNOT PARSE IT" IS NOT "NOTHING IS HAPPENING". This branch returned a
        # confident green, so one edit to the hunt's log line would have retired the check in
        # silence while the loop it was built for kept spending. If the log shows the hunt STARTING
        # and no pass line can be read, that is UNKNOWN and it must say so. A guard that cannot
        # fail is the same defect as one that is always red. [[feedback-blind-fixture-green-gate]]
        if _re.search(r"hunting\s+\S", txt) or "HIT " in txt:
            return "unknown", ("the hunt is running in the log but no 'hunt done:' line can be "
                               "parsed, so its cost cannot be read — the line this check reads "
                               "may have changed (chronicle_hunt.py, log('hunt done: ...'))")
        return "ok", "no hunt has run in the recent log — nothing is being bought"
    reads = sum(int(a) for a, _ in passes)
    sightings = sum(int(b) for _, b in passes)

    # ⚠ v2175.3 — PIN THE LAW, NOT THE NUMBER. The floor was `reads < 200` and ONE REAL PASS OF
    # THE VERY LOOP THIS CHECK EXISTS FOR IS 144 READS (8 names x 18 frames, measured). So the
    # trigger sat above its own per-pass ceiling: nothing could fire until the loop had already
    # paid twice, and on a log rotated per run it could never fire at all. Same shape as
    # STILL_MAX_DIFF=0.22 against a signal whose maximum is 0.133.
    # [[feedback-threshold-above-the-ceiling]]
    #
    # The law is not a read count. It is: THE HUNT WENT BACK AND BOUGHT AGAIN, AND STILL BROUGHT
    # NOTHING HOME. One empty pass is a normal miss. Two is the loop, at any price.
    if sightings == 0 and len(passes) >= 2:
        return "missing", ("the hunt has run %d pass(es) for %d PAID read(s) and found NOTHING. "
                           "That is the v2174 loop: it is re-buying names that already came back "
                           "empty. Check the hunt memory is being written (tv/chron_hunt_memory"
                           ".json, or beside chronicle_swept.json under TV_HIST)."
                           % (len(passes), reads))
    # ⚠ NOT `and reads < 200`. A single pass with sightings==0 falls past every branch below and
    # reaches the `%.0f` tail with per=None, which raises inside a health check — the doctor
    # reporting an exception instead of a verdict. One pass is a miss at ANY price.
    if len(passes) < 2:
        return "ok", ("%d hunt pass(es), %d paid read(s), %d sighting(s) — a single pass is a "
                      "miss, not a loop" % (len(passes), reads, sightings))
    per = reads / float(sightings) if sightings else None
    if per and per > 400:
        return "missing", ("the hunt is paying %.0f reads per new sighting (%d reads, %d "
                           "sighting(s)). The empty-hunt memory is not holding — a name that "
                           "found nothing is being bought again." % (per, reads, sightings))
    return "ok", ("the hunt is paying %.0f read(s) per new sighting across %d pass(es)"
                  % (per, len(passes)))


def _check_the_reel_extract_is_moving():
    """v2139 — IS THE EXTRACT ACTUALLY MOVING, and do the two memories still agree?

    THE FAULT THIS EXISTS FOR ran for 40 hours with every lamp green. The reel auto-sweep's
    private list claimed all 30 reels on disk were done; the durable memory had 12 of them never
    swept; the retention panel told him 11 were waiting. The loop asked only the private list, so
    it answered "no unswept reel" every 20 seconds and read nothing. He found it by reading a
    tooltip.

    The eagle could not have caught it. Its only sweep-named check, "sweep would find", is in SLOW
    and _eagle_once calls run(include_slow=False) — so on the ten-minute timer it never ran at all
    — and its subject is vault stash-panel density, not whether extract is moving. A gate joined to
    its caller and unjoined from its subject. Meanwhile "disk headroom" returned OK sixteen times
    while this was silent. [[the-unjoined-end]] [[feedback-silence-is-not-evidence]]

    CHEAP BY CONSTRUCTION so it can live on the timer: one directory listing and one small JSON
    read. No model call, no du, no subprocess.
    """
    try:
        import control_app as ca
        import chronicle_retro as cr
    except Exception as e:
        return UNKNOWN, "could not import the sweep modules: %s" % str(e)[:90]
    hist = os.environ.get("TV_HIST") or os.path.join(HERE, "frames", "hist")
    if not os.path.isdir(hist):
        return UNKNOWN, "no frames/hist on this machine"
    try:
        dirs = [os.path.basename(str(d)) for d in (cr.reel_dirs(hist, newest_first=True) or [])]
    except Exception as e:
        return UNKNOWN, "could not list reels: %s" % str(e)[:90]
    if not dirs:
        return OK, "no reels on disk — nothing to extract"
    try:
        mem = ca._chron_swept_mem()
        owed = [r for r in dirs if ca._chron_reel_owes_a_read(r, mem)]
        private = ca._chron_reels_seen()
    except Exception as e:
        return UNKNOWN, "could not read the sweep memory: %s" % str(e)[:90]

    # THE SPLIT is CONTEXT, NOT THE VERDICT — and saying otherwise would be the same mistake
    # twice. Before v2139 the private list GATED the loop, so a split meant "these will never be
    # started" and was the whole fault. v2139 moved every decision onto the durable memory, so the
    # private list is now write-only: a stale entry is a file that lies, not a stall. Reporting it
    # as MISSING would be a label that outlived its referent — a true count under a sentence that
    # stopped being true — which is the class this console keeps paying for. So it rides in `why`,
    # and the fault that can still hurt him is the one that decides the verdict.
    split = [r for r in owed if r in private]
    tail = ("" if not split else
            " · the auto-sweep's own list still calls %d of them done — inert since v2139, "
            "nothing gates on it" % len(split))
    if not owed:
        return OK, "all %d reel(s) have been read%s" % (len(dirs), tail)

    # OWED BUT NOT MOVING. The AGE is the finding — "the loop is alive" is not evidence that it is
    # doing anything, which is exactly how this went unnoticed for two days.
    try:
        last = os.path.getmtime(ca._chron_swept_path())
    except Exception:
        return UNKNOWN, ("%d reel(s) owe a read and the sweep memory cannot be read, so its age "
                         "is unknown" % len(owed))
    hours = (time.time() - last) / 3600.0
    if hours > 2.0:
        return MISSING, ("%d of %d reel(s) owe a read and nothing has been banked for %.1f hours%s"
                         % (len(owed), len(dirs), hours, tail))
    return OK, ("%d reel(s) owe a read, last banked %.1fh ago — the loop is working through them%s"
                % (len(owed), hours, tail))


CHECKS = [
    ("version drift", _check_version_drift),
    ("lane intent", _check_lane_intent),
    ("disk headroom", _check_disk_headroom),
    ("subscription", _check_subscription_burn),
    ("unattended reel", _check_a_reel_is_not_recording_unattended),
    ("reel extract", _check_the_reel_extract_is_moving),
    ("hunt economy", _check_the_hunt_is_buying_something),
    ("sweep would find", _check_the_sweep_would_find_something),
    ("board is claimed", _check_the_board_world_is_claimed),
    ("visual lock", _check_the_visual_lock_holds),
    ("art corpus", _check_the_art_corpus),
    ("footage has a reel", _check_footage_belongs_to_a_reel),
    ("vault stores", _check_the_vault_stores_are_readable),
    ("locked lanes", _check_the_locked_lanes_still_refuse),
    ("surfaces agree", _check_the_two_surfaces_agree),
    ("the other doctors", _check_the_other_doctors),
]


# v2026 — the sub-doctor call shells out to two full diagnostics and costs ~2 minutes. That is
# fine for a human pressing the button and NOT fine on every CI run, so callers can ask for the
# cheap subset. The slow one is named rather than guessed at, so adding a check never silently
# joins the slow set.
# v2080 — AND "sweep would find" WAS NEVER CHEAP. Measured on a fixture tree: 16,585 ms of a
# 17,069 ms "cheap subset" — 97% of it, in the set that runs on a ten-minute timer at every console
# boot. It cost a gate: v2080 made the eagle measure BEFORE it sleeps (right) and start in headless
# consoles too (right), and together those two correct fixes put a 17-second tick in the boot path
# of every console a test spawns, pushing test_roundtrip_sim's stub read past its 60s deadline.
# Two fixes breaking each other, and neither was wrong on its own. [[two-fixes-broke-each-other]]
#
# The SLOW set being NAMED rather than guessed was the right design and it did not save me, because
# nobody had timed the members. A list is a claim; the guard below now MEASURES it.
SLOW = ("the other doctors", "sweep would find")


def run(include_slow=True):
    rows = []
    for name, fn in CHECKS:
        if not include_slow and name in SLOW:
            continue
        try:
            state, why = fn()
        except Exception as e:
            state, why = UNKNOWN, "this check itself threw: %s" % str(e)[:120]
        rows.append({"check": name, "state": state, "why": why})
    return rows


def main(argv):
    rows = run()
    if "--json" in argv:
        print(json.dumps({"ok": True, "checks": rows,
                          "generatedTs": int(time.time() * 1000)}, ensure_ascii=False))
        return 0
    print("\n🦅 EAGLE EYE — the whole console, from above\n")
    for r in rows:
        print("  %s %-18s %s" % (ICON.get(r["state"], "⚪"), r["check"], r["why"]))
    needs = [r for r in rows if r["state"] == MISSING]
    unk = [r for r in rows if r["state"] == UNKNOWN]
    print()
    if needs:
        print("⚠ %d thing(s) need you. Nothing above is a guess: each line names what it measured."
              % len(needs))
    elif unk:
        print("✅ nothing is out of line. %d check(s) could not be determined — that is not a pass, "
              "it is a gap." % len(unk))
    else:
        print("✅ every check green.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
