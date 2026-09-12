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
import contextlib
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

OK, MISSING, UNKNOWN, UNMEASURED = "ok", "missing", "unknown", "unmeasured"
ICON = {OK: "🟢", MISSING: "🟠", UNKNOWN: "⚪", UNMEASURED: "◻"}
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


#: ⚠ ONE READ OF HIS LIVE BOARD PER TICK. THREE checks now need /api/board_ownership, and that
#: route EVALUATES JAVASCRIPT IN THE WINDOW HE IS LOOKING AT. Two of the three predate this fold —
#: so the rail was already poking his board twice every ten minutes and nothing said so. Asking
#: three times buys no new information. Short TTL, so a human pressing the button twice still gets
#: a fresh answer. [[borrowed-surface]] — his window is not free to poke.
#: ⚠ SHARED FOR THE LENGTH OF ONE TICK, NEVER LONGER. My first cut memoised on a 5-SECOND TTL and
#: broke EIGHT existing guards at once — they stub `_post` and call a check directly, and a
#: module-level cache swallows the stub and serves the previous test's answer. THE COUNT WAS THE
#: TELL: eight failures from one edit is a shape mistake, not eight defects. So the share is scoped
#: to `run()`, which is the only place three checks are asked back to back; a check called on its
#: own always reads fresh, which is what every caller outside the rail expects.
#: [[feedback-suspect-the-instrument]]
_board_cache = {"active": False, "got": None}


def _board_read():
    if _board_cache["active"]:
        return _board_cache["got"]
    return _post("/api/board_ownership", {"sample": 0})


def _check_the_board_world_is_claimed():
    """An UNCLAIMED board lives in a guest world, and everything applied there is lost.

    This is the failure that cost a whole night: `bible.html` resolves `_D2R_OWNER` only from a
    clicked `d2r_ownerClaim`. Without it `_D2R_PFX` becomes 'I·<installId>·' — a per-install world.
    An apply into it returns ok:true, writes real rows, and they are unreachable from the next load.

    It is SILENT BY CONSTRUCTION: the ledger counts read exactly the same in a doomed world as in a
    real one, so nothing on any screen distinguishes them. That is precisely what a doctor is for.
    [[the-unjoined-end]]
    """
    got = _board_read()
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


def _check_behind_the_fleet():
    """IS THIS CHECKOUT BEHIND ORIGIN? The one kind of out-of-sync nothing here could see.

    ⚠ "version drift" IS A DIFFERENT QUESTION AND IT PASSES WHILE THIS FAILS. That check compares
    the RUNNING process against the TREE ON DISK. Dean's console sat at v2161 while origin was at
    v2246 — 85 versions — and drift was GREEN the whole time, correctly: his process and his disk
    agreed with each other. They were simply agreeing on old bytes. Konyo, on the phone with him:
    "there is no reason he isnt on my version and we arent synced." Nothing in these 22 checks
    asked the only question that would have caught it. [[the-unjoined-end]]

    ⚠ AND IT MUST NOT FETCH. The obvious implementation asks /api/update, which force-fetches, so
    it would belong in SLOW — and SLOW is exactly where "sweep would find" went to die: the eagle
    runs with include_slow=False, so a SLOW check never runs on the timer at all. This one reads
    the origin/main ref that is already on disk, which costs nothing and runs every tick. The
    console's own fleet banner refreshes that ref every 15 minutes (control_ui.html, v2248).

    ⚠ SO THE ANSWER CARRIES THE AGE OF THE REF, NOT THE AGE OF THE READ. "0 behind" against a ref
    last fetched three days ago means "0 behind what I knew three days ago", and saying it plainly
    is the difference between a fact and a reassurance. [[stale-reading]]
    """
    import subprocess as _sp
    import time as _t

    def _git(*args):
        try:
            r = _sp.run(("git",) + args, cwd=ROOT, capture_output=True, text=True, timeout=15)
            return (r.stdout or "").strip() if r.returncode == 0 else None
        except Exception:
            return None

    if not os.path.isdir(os.path.join(ROOT, ".git")):
        return UNKNOWN, "this install is not a git checkout, so there is no origin to be behind"
    if _git("rev-parse", "--verify", "--quiet", "origin/main") is None:
        return UNKNOWN, "no origin/main ref on disk yet — nothing has ever fetched here"

    # how old is what we are comparing against?
    age = ""
    for nm in ("FETCH_HEAD", os.path.join("refs", "remotes", "origin", "main")):
        p = os.path.join(ROOT, ".git", nm)
        if os.path.exists(p):
            mins = int(max(0, _t.time() - os.path.getmtime(p)) // 60)
            age = ("%d min" % mins) if mins < 120 else ("%.1f h" % (mins / 60.0))
            break
    against = (" (against an origin/main ref last refreshed %s ago)" % age) if age else \
              " (the age of that ref is UNKNOWN)"

    behind = _git("rev-list", "--count", "HEAD..origin/main")
    if behind is None or not behind.isdigit():
        return UNKNOWN, "could not count the commits between this checkout and origin/main"
    n = int(behind)
    if n == 0:
        return OK, "this checkout is level with origin/main%s" % against
    return MISSING, ("this checkout is %d commit%s behind origin/main%s. The console pulls on its "
                     "own every 15 minutes and restarts itself when the new build lands; if it has "
                     "not, the fleet banner's UPDATE NOW does it, or: git pull --ff-only"
                     % (n, "s" if n != 1 else "", against))


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


def _check_the_evidence_ledger_is_readable():
    """v2730 — 310 NAMES OF TESTIMONY AND NOTHING WAS LOOKING AT THEM.

    Konyo: *"the join the heart of the console connect and wire whatever is needed so its all not
    in the dark"*. `chron_evidence.json` is what makes cross-reel corroboration possible — its own
    writer says so — and no Doctor row, no invariant and no census entry mentioned it.

    ⚠ AN UNREADABLE LEDGER MUST NEVER READ AS AN EMPTY ONE. v1779 recorded the real event: one
    torn read returned {}, the merge saved {} as the whole accumulated ledger, and every sighting
    ever collected was gone with nothing on any screen to say so.
    ⚠ AND THE TELL IS INTERNAL: `pagesRead` counts pages the reader got through. Pages banked with
    ZERO names left is not a quiet day — it is the signature of a ledger that was emptied after
    the reading happened. That comparison is free and it is the one this row exists to make.
    """
    import json as _j
    fp = os.path.join(HERE, "chron_evidence.json")
    if not os.path.exists(fp):
        return UNKNOWN, ("chron_evidence.json has never been written — there is no testimony to "
                         "lose yet, which is different from having lost it")
    try:
        with open(fp, encoding="utf-8") as fh:
            ev = _j.load(fh)
    except Exception as e:
        return MISSING, ("chron_evidence.json will not parse (%s) — every sighting ever banked is "
                         "INCOMPLETE, not empty, and nothing downstream may treat it as zero"
                         % str(e)[:60])
    if not isinstance(ev, dict):
        return MISSING, ("chron_evidence.json is a %s, not an object — the ledger's shape is gone"
                         % type(ev).__name__)
    n_u = len(ev.get("uniques") or {})
    n_s = len(ev.get("sets") or {})
    pages = ev.get("pagesRead")
    if (n_u + n_s) == 0 and isinstance(pages, int) and pages > 0:
        return MISSING, ("%d page(s) were read and banked, and the ledger now holds ZERO names — "
                         "that is the v1779 shape: a ledger emptied after the reading happened"
                         % pages)
    return OK, ("%d unique(s) and %d set(s) carry testimony across %s page(s) read"
                % (n_u, n_s, pages if pages is not None else "an unrecorded number of"))


def _check_the_ledger_backup_covers_every_store():
    """v2730 — THE AUTOMATIC BACKUP HAS NEVER CAPTURED TWO OF HIS SIX LEDGERS.

    MEASURED on his 60 real backup files, 2026-09-06: every one carries foundLog (419), owned (169)
    and setPieces (123) — and NOT `rwMade` (his 99 runewords) or `gameFound` (29). No file records
    which PROFILE it came from either.

    ⚠⚠ AND IT BLINDS A WATCHER. tv/ledger_highwater.py ratchets
    KEYS = (foundLog, setPieces, rwMade, owned) against each key's historic max — but since no
    snapshot has ever carried `rwMade`, that column can only read UNKNOWN, forever, and an UNKNOWN
    column looks exactly like a column with nothing wrong. A backup that runs every ten minutes and
    writes a plausible file is the most convincing kind of gap there is.
    [[unknown-stays-unknown]] [[the-unjoined-end]]
    """
    import json as _j, glob as _g
    d = os.path.expanduser("~/d2r_ledger_backups")
    if not os.path.isdir(d):
        return UNKNOWN, "no ledger-backup directory yet — nothing has been snapshotted"
    files = sorted(_g.glob(os.path.join(d, "ledger_*.json")), key=os.path.getmtime, reverse=True)
    if not files:
        return UNKNOWN, "the backup directory is empty — no snapshot has ever been written"
    try:
        with open(files[0], encoding="utf-8") as fh:
            b = _j.load(fh)
    except Exception as e:
        return MISSING, ("the newest ledger backup will not parse (%s) — the copy of his ledgers "
                         "cannot be trusted" % str(e)[:50])
    led = (b.get("ledger") or {}) if isinstance(b, dict) else {}
    WANT = ("foundLog", "owned", "setPieces", "rwMade", "gameFound")
    missing = [k for k in WANT if k not in led]
    routed = any(k in (b or {}) for k in ("route", "profile", "who", "machine"))
    if missing:
        return MISSING, ("the newest backup carries %d of %d ledgers — MISSING %s. Those stores "
                         "have no automatic copy at all, and ledger_highwater ratchets rwMade "
                         "against snapshots that never contain it."
                         % (len(WANT) - len(missing), len(WANT), ", ".join(missing)))
    if not routed:
        return MISSING, ("the newest backup records no route/profile, so nothing says WHOSE "
                         "ledgers it holds and a restore cannot tell one profile from another")
    return OK, ("the newest backup carries all %d ledgers and names its profile (%d file(s) kept)"
                % (len(WANT), len(files)))


#: What the backup loop is allowed to have done last. Anything else is a REFUSAL, and a refusal
#: repeating every ten minutes is an outage. ⚠ Kept as a closed allowlist rather than a list of
#: known error strings: an unrecognised message must read as a failure, never as "probably fine".
_BACKUP_BENIGN = ("wrote ", "unchanged since")


def _check_the_backup_loop_is_actually_WRITING():
    """v2735 — THE BACKUP LOOP REFUSED EVERY SNAPSHOT FOR A DAY AND NOTHING ASKED.

    Konyo, on being shown the restore wire: *"and all connected to the heart of the console
    obviously right? is it needed?"* — this check is the answer, and it went RED the moment it
    existed.

    MEASURED on his live console, 2026-09-06 18:15:

        ledgerBackup.writes   0
        ledgerBackup.why      "Can't find variable: dump"
        newest backup file    80 minutes old, still the pre-v2731 three-store shape

    v2731 added `rwMadeFull:(dump?rwFull:null)` to the board read. No such JS variable exists —
    `dump_stores` is interpolated as a bare true/false LITERAL — so the entire read threw and every
    snapshot was refused from that ship onward.

    ⚠⚠ EVERY GATE WAS GREEN THROUGHOUT, and correctly:
    `test_ledger_backup_covers_every_store` grades the SOURCE, and source is not a running board.
    The refusal existed in exactly one place — a string in `_LEDGER_BACKUP_STATE["why"]`, published
    at `/api/status.ledgerBackup` and read by NOBODY. A loop that fails silently every ten minutes
    is indistinguishable from a loop with nothing to do, and the newest file it left behind looks
    like a healthy backup right up until the day it is needed.
    [[the-unjoined-end]] [[feedback-verify-not-proxy]] [[zero-needs-a-denominator]]

    THE LAW: the last thing the loop did must be a write or a benign skip. Not "no exception was
    raised" — the loop swallows everything by design so one bad read cannot end it.
    """
    # ⚠ 15s, NOT the 4s default. MEASURED: /api/status takes 11.6s COLD and 0.26s warm — it folds
    # a fleet read and a drift check. At the default this check reported "the console is not
    # answering" against a console that was answering fine, which is a false UNKNOWN blaming the
    # wrong thing, and it is how a real red would get dismissed as flakiness. [[stale-reading]]
    st = _get("/api/status", timeout=15)
    if not isinstance(st, dict) or not st.get("ok"):
        return UNKNOWN, ("the console did not answer /api/status within 15s, so what the backup "
                         "loop last did is UNMEASURED — which is not the same as healthy")
    lb = st.get("ledgerBackup")
    if not isinstance(lb, dict):
        return MISSING, ("/api/status no longer publishes `ledgerBackup`, so the only place the "
                         "backup loop's refusals are visible is gone and this check is blind")
    why = str(lb.get("why") or "")
    writes = lb.get("writes")
    if writes is None:
        return UNKNOWN, "the backup state reports no write count, so nothing can be concluded"
    if not why:
        # ⚠ A GENUINE UNKNOWN, NOT A PASS. The first snapshot comes 45s after boot; before that the
        # loop has done nothing and has nothing to report. Grading that as OK would make a
        # freshly-restarted console always look healthy — the one moment it is least proven.
        return UNKNOWN, ("the loop has not reported a snapshot yet (%d write(s) so far) — too early "
                         "to say, and that is not the same as working" % int(writes or 0))
    # ⚠⚠ v2736 — `why` IS STICKY, AND WITHOUT THIS THE WHOLE CHECK WAS DEFEATED BY A DEAD LOOP.
    # REPRODUCED: a loop that wrote once and then stopped three days ago left
    # why="wrote ledger_2026-09-03_010101.json" in place, and this row graded it **OK**. Nothing
    # clears the string, and the loop swallows every exception by design so one bad read cannot
    # end it — so the last benign message outlives the loop that wrote it.
    # Found by handing the shipped diff to a different model family and asking it to refute.
    # ⚠ THIS IS [[stale-reading]] COMMITTED INSIDE THE WATCHER BUILT TO CATCH A SILENT FAILURE:
    # the age of the THING, not the age of the fetch. The message was fresh; the act was not.
    try:
        age_ms = lb.get("lastTryMs")
        if age_ms is None:
            return UNKNOWN, ("the loop publishes no last-attempt time, so whether it is still "
                             "running is UNMEASURED — a sticky `why` cannot answer it")
        age_s = max(0.0, time.time() - (float(age_ms) / 1000.0))
    except (TypeError, ValueError):
        return UNKNOWN, "the loop's last-attempt time is unreadable, so its liveness is UNKNOWN"
    # three intervals: one missed tick is scheduling noise, three is a loop that is gone
    if age_s > 3 * 600:
        return MISSING, ("the backup loop has not RUN for %d minute(s) — it fires every 10, so it "
                         "is not running at all. Its last message is %r, which is sticky and says "
                         "nothing about whether the loop still exists."
                         % (int(age_s / 60), why[:60]))
    if not why.startswith(_BACKUP_BENIGN):
        return MISSING, ("the backup loop is REFUSING every snapshot: %r. It has written %d file(s) "
                         "this run, and it retries every %d minutes, so this repeats silently. His "
                         "ledgers have no fresh automatic copy while this stands."
                         % (why[:90], int(writes or 0), 10))
    return OK, ("the loop's last act was %r after %d write(s) this run"
                % (why[:60], int(writes or 0)))


#: Stations that owe something NO automatic lane can deliver, and why each is by design rather than
#: a gap. ⚠ Without this split the row cries wolf on 40 of 40 and gets ignored — and a distrusted
#: instrument is a switched-off instrument, which is how the defects below survived in the first place.
_BY_DESIGN_STATIONS = {
    "JOIN": "sealed AND the names are on disk; the seal does not carry them — that is a CODE change",
    # ⚠ v3020 — NOT REG-340. That rules the CHARACTER name; these reels lack ITEM names, and an
    # item's name is only ever in its tooltip. The capture that helps is HOVER, not the C panel.
    "CAPTURE": "the capture itself must change — HOVER coverage so the tooltips that carry item "
               "names are filmed — not the lane that reads it",
}


def _check_read_names_are_actually_banked():
    """v2751 — 119 ITEM NAMES WERE READ FROM HIS FOOTAGE AND NONE OF THEM ARE BANKED.

    Konyo, 2026-09-07: *"the routing and funnel and main pipeline should still go through it
    regardless of the paid reads.. i want it filtered and then stamped unified logic"*. Following
    that instead of the paid-read question is what found this.

    MEASURED across all 40 reels, printer.stream() joined to reel_router.route():
        PRINTER   11 reels   64 names read, and the session carries NO SEAL AT ALL
        JOIN       4 reels   55 names read, sealed — and the seal does not carry them
        CAPTURE/EMPTY/STATION            0 names
    The printer says it per reel: *"23 item name(s) were read, but this session has no seal at all,
    so the extraction contract was never even asked about it."*

    ⚠⚠ THE READING ALREADY HAPPENED. The names are in the JOURNAL RING right now, retrievable by
    session id — Andariel's Visage, Atma's Wail, Bartuc's Cut-Throat, Sandstorm Trek, Tearhaunch.
    No paid read is owed for any of them; the pipeline is stalled AFTER the read.

    ⚠ AND HIS FILTER DECIDES WHICH ONES COUNT, which is why this row reports PANEL separately.
    extract_gap's taxonomy (his own words: *"if its a FLOOR ITEM with no stash/inventory open then
    obviously it cant be in the same exact route"*) splits 472 corpus names PANEL 110 / FLOOR 208 /
    CHRONICLE 154 — 77% filtered. A floor name has no cell to name, so it is a sighting and not a
    holding. Reporting one number over both would overstate the work owed.

    ⛔ IT REPORTS AND NEVER WRITES. Banking means landing in vault_accum/vault_seen, which is gated
    on witnesses deliberately, and footage has no un-delete. This row makes the stall visible; the
    existing witnessed machinery stays the only thing that writes.
    """
    try:
        import printer as _P, reel_router as _RR, extract_gap as _EG
    except Exception as exc:
        return UNKNOWN, ("the printer/router could not be imported (%s), so whether read names are "
                         "banked is UNKNOWN" % type(exc).__name__)
    try:
        rep, rt = _P.stream(), _RR.route()
    except Exception as exc:
        return UNKNOWN, "the printer or router raised (%s) - UNKNOWN, not clean" % type(exc).__name__
    if not isinstance(rep, dict) or not isinstance(rt, dict) or not rt.get("ok"):
        return UNKNOWN, "the printer or router would not answer, so nothing is known about banking"
    st = {x.get("reel"): x.get("station") for x in (rt.get("reels") or [])}
    unsealed = sealed_blind = 0
    reels = set()
    for r in (rep.get("rows") or []):
        ex = ((r.get("stations") or {}).get("extract") or {})
        n, sld = ex.get("names"), ex.get("sealed")
        if not isinstance(n, int) or not n:
            continue
        s = st.get(str(r.get("reel")))
        if sld is False:
            unsealed += n; reels.add(str(r.get("reel")))
        elif s == "JOIN":
            sealed_blind += n; reels.add(str(r.get("reel")))
    total = unsealed + sealed_blind
    if not total:
        return OK, "every item name the readers produced is carried by a seal"
    # his filter: only PANEL names can become a holding
    panel = None
    try:
        named, _why = _EG._named_sessions()
        panel = sum(int((v or {}).get("panel") or 0) for v in (named or {}).values())
    except Exception:
        panel = None
    tail = ("" if panel is None else
            " Of the corpus's names, %d were read with a container OPEN (stash/inventory) and can "
            "become a holding; the rest are floor sightings with no cell to name." % panel)
    return MISSING, ("%d item name(s) were READ from %d reel(s) and NONE are banked: %d sit in "
                     "sessions with NO SEAL AT ALL, and %d are under a seal that does not carry "
                     "them. The reading already happened - the names are in the journal ring - so "
                     "no paid read is owed here.%s"
                     % (total, len(reels), unsealed, sealed_blind, tail))


def _check_the_printer_can_reach_the_corpus():
    """v2749 — ZERO CONTRADICTIONS BECAUSE THE CONTRACT REFUSES EVERY SEAL.

    His ask, 2026-09-03: *"i want this related to the 3/4D printer it should be in the same zone.
    that unified printer needs to be built, that processing system for the reels all need a unified
    logic coming in and out"*. `printer_reach` answers the question that opens: HOW MUCH OF THE
    CORPUS CAN THE PIPELINE ACT ON AT ALL. Nothing read it — `grep -c printer_reach` was 0 across
    control_app.py, console_doctor.py, corroborate.py and control_ui.html, the same shape as
    end_routes one version ago. [[the-unjoined-end]] [[sweep-dont-ask]]

    MEASURED on his tree: reels 437 · seals 31 · joined 21 · **sealsSatisfyingContract 0**, with
    name, location AND provenance missing on all 31.

    ⚠⚠ THE READING THAT MAKES THIS WORTH A ROW: a downstream reader sees ZERO CONTRADICTIONS and
    concludes the pipeline is healthy. It is not — the contract refuses every seal, so the
    contradiction CANNOT ARISE. A zero that means "nothing qualified" wearing the clothes of a zero
    that means "nothing wrong". [[zero-needs-a-denominator]]

    ⚠ IT NAMES THE MISSING FACTS, never a bare count, because the facts imply DIFFERENT WORK: a
    missing `name` is a reader change, while a missing `location` is a CAPTURE question — 0 of 1,065
    deep rows carry a cell — and that is HIS ruling, not something code decides.
    ⛔ No wilson lock: reachability is a READING, not a claim attacks can refute.
    """
    try:
        import printer_reach as _PR
    except Exception as exc:
        return UNKNOWN, ("printer_reach would not import (%s), so how much of the corpus the "
                         "pipeline can reach is UNKNOWN" % type(exc).__name__)
    try:
        r = _PR.report()
    except Exception as exc:
        return UNKNOWN, "the printer-reach report raised (%s) - UNKNOWN, not clean" % type(exc).__name__
    if not isinstance(r, dict) or not r.get("counts"):
        # ⚠ `(r or {}).get(...)` RAISES when r is a truthy NON-dict — a bare string report walks
        # straight past the isinstance guard and into AttributeError. Caught by this row's own gate
        # before it shipped: an UNKNOWN path that crashes reports nothing, which is strictly worse
        # than the unknown it was written to express. [[unknown-stays-unknown]]
        _why = r.get("why") if isinstance(r, dict) else None
        return UNKNOWN, str(_why or "the printer-reach report carried no counts")
    c = r.get("counts") or {}
    seals = c.get("seals")
    ok_n = c.get("sealsSatisfyingContract")
    if seals is None or ok_n is None:
        # a count nobody took is not zero
        return UNKNOWN, "the report carried no seal counts, so nothing is known about reach"
    if ok_n:
        return OK, ("%s of %s seal(s) satisfy the extraction contract, so the pipeline can act on "
                    "the corpus" % (ok_n, seals))
    facts = r.get("missingByFact") or {}
    named = ", ".join("%s %s" % (k, v) for k, v in sorted(facts.items(), key=lambda kv: -kv[1]))
    return MISSING, ("NOT ONE of %s seal(s) satisfies the extraction contract, so no reel can be "
                     "judged disposable and a contradiction cannot arise AT ALL - zero here means "
                     "the contract refused everything, not that nothing is wrong. Missing: %s. "
                     "(reels %s, joined %s.) ⚠ `location` is a CAPTURE question, not a reader one."
                     % (seals, named or "unrecorded", c.get("reels"), c.get("joined")))


def _check_every_reel_can_still_reach_an_end_route():
    """v2748 — THE DERIVED END-ROUTE PREDICATE WAS READ BY NOTHING.

    MEASURED before writing this: `grep -c end_routes` was **0** in control_app.py, console_doctor.py,
    corroborate.py and control_ui.html. Built, correct, covered by 27 of its own tests, and invisible
    to every surface and every supervision layer — the SAME defect this heart caught in reel_router
    one version ago, in its sibling. I fixed the river's unjoined end and left its twin running.
    [[the-unjoined-end]] [[sweep-dont-ask]]

    Konyo's ruling settled the DESTINATION and named the METHOD: *"it should be also eventually
    tombstoned though why is not also processed through the printer to get routed back at the end
    routes they should. reverse engineeer it if needed the ones that are working"*. So the door was
    read back off the 410 reels that already went through it, not invented — 99.27% coverage against
    a declared floor of 95%.

    ⚠⚠ THE SPLIT THIS ROW EXISTS TO KEEP VISIBLE, because collapsing it is how 40 reels became one
    undifferentiated bucket:
      · DEAD-ENDED     every door refused, with numbers. THIS is what his ruling forbids.
      · FINISHED-WAITING  a door OPENED and only circumstance holds it. His ruling does not forbid
                          this, and counting it here would make the row read 40 of 40 — true,
                          useless, and ignored within a week.

    ⚠ RED TODAY ON PURPOSE, at 32 of 40. A check that could only ever be green measures nothing. It
    goes green when reels stop dead-ending, not when someone edits a list.
    ⛔ NO WILSON LOCK: "these reels cannot reach an end route" is a READING, not a claim attacks can
    refute. Manufacturing attacks to score a state is the inflation `_hardening_gap` refuses.
    """
    try:
        import end_routes as _ER
    except Exception as exc:
        return UNKNOWN, ("end_routes would not import (%s), so whether any reel can reach an end "
                         "route is UNKNOWN" % type(exc).__name__)
    try:
        r = _ER.report()
    except Exception as exc:
        return UNKNOWN, "the end-route report raised (%s) - UNKNOWN, not clean" % type(exc).__name__
    # ⚠ SAME SHAPE AS THE printer-reach ROW, found by sweeping this file the moment that one was
    # fixed rather than a version later. `r.get("ok")` raises on a truthy NON-dict, and so does the
    # `(r or {})` fallback beside it — so an UNKNOWN path written to survive a bad report would
    # itself crash on one. An UNKNOWN that raises reports nothing at all. [[sweep-dont-ask]]
    if not isinstance(r, dict) or not r.get("ok"):
        _why = r.get("why") if isinstance(r, dict) else None
        return UNKNOWN, str(_why or "the end-route report could not be taken")
    dead = r.get("deadEnded")
    waiting = r.get("finishedWaiting")
    walked = r.get("walked")
    if dead is None or walked is None:
        # a count nobody took is not zero
        return UNKNOWN, "the report carried no dead-ended count, so nothing is known"
    if not dead:
        return OK, ("no reel is dead-ended: %s of %s finished and waiting only on circumstance"
                    % (waiting, walked))
    # name WHAT they lack — a count alone is not actionable
    lack = {}
    for x in (r.get("rows") or []):
        if not x.get("deadEnded"):
            continue
        for g in (x.get("missing") or []):
            w = g.get("what") if isinstance(g, dict) else str(g)
            lack[str(w)] = lack.get(str(w), 0) + 1
    named = ", ".join("%s %d" % (k, v) for k, v in sorted(lack.items(), key=lambda kv: -kv[1]))
    return MISSING, ("%s of %s reel(s) are DEAD-ENDED - every end-route door refused them, with "
                     "numbers. What they lack: %s. (%s more are finished and waiting only on "
                     "circumstance, which his ruling does not forbid.)"
                     % (dead, walked, named or "unrecorded", waiting))


def _check_the_console_painted_all_of_itself():
    """v2747 — THE WITNESS COULD NOT SEE HALF A BLANK CONSOLE, AND HIS SIGHTING WAS EXACTLY THAT.

    Konyo, 2026-09-06, with a screenshot: *"theres a big empty space here im pretty sure there was
    something here"*. The Sessions tab's right rail rendered correctly — relaunch, eagle, repair,
    THE FLEET, THE SHELF — while ~1080x560 of the MAIN COLUMN was blank.

    ⚠⚠ THE BLINDNESS IS MEASURED, NOT ARGUED. `paint_witness.blank_strikes` asks about the WHOLE
    WINDOW: *"look N of M found content ON THE WINDOW, so it is not blank"*. His rail was painting,
    so the window HAD content, so the witness said PAINTED — correctly, for the question it asks.
    `tv/ui_faults.jsonl` settles it: on the day of the sighting it recorded 21 faults, SIXTEEN of
    them `console-pixels-blank-nothing-else-saw-it`, and ZERO within 45 minutes of 20:14. The
    instrument was working and blind at the same time. [[gate-blind-to-unexercised-input]]

    ⚠ THIS ROW READS A STATE, IT DOES NOT ACT. region_witness never focuses, reloads or restarts —
    the rescue decides. A witness that acts is a witness nobody can trust to abstain.
    ⚠ AND IT ABSTAINS OFTEN, ON PURPOSE: an OCCLUDED window (Safari over his console) or a failed
    capture is UNKNOWN, never OK and never a fault. Measured live — Safari and Terminal covered
    100% of his console while this was being built, and a one-sided cover would otherwise have
    read blank-left/painted-right and fired about a perfectly healthy window.
    """
    try:
        import region_witness as _RW
    except Exception as exc:
        return UNKNOWN, ("the region witness would not import (%s), so nothing is known about "
                         "which parts of the console painted" % type(exc).__name__)
    pid = os.getpid()
    try:
        r = _RW.half_blank_strikes(pid)
    except Exception as exc:
        return UNKNOWN, ("the region witness raised (%s) - UNKNOWN, not clean"
                         % type(exc).__name__)
    if not r.get("ok"):
        # a covered or unphotographable window is not evidence about painting
        return UNKNOWN, str(r.get("why") or "the window could not be looked at")
    # ⚠⚠ v2752 — "NOT PARTLY DRAWN" IS TWO OPPOSITE FACTS AND THIS RETURNED OK FOR BOTH.
    # region_witness answers half=False both when everything is drawn AND when NOTHING is, because
    # a fully blank window is the whole-window witness's job. MEASURED on his black console: all six
    # cells blank, ink 0.0000 — and this row returned OK, while paint_witness said PAINTED off two
    # rows of title-bar border. Two instruments, one blind and one deferring to it, and a black
    # screen reported no fault at all. The deferral is still right about WHO RESCUES; it was wrong
    # about staying silent. [[the-unjoined-end]] [[unknown-stays-unknown]]
    if not r.get("half"):
        _g = r.get("grid") or {}
        _b, _p = _g.get("blank"), _g.get("painted")
        if isinstance(_b, int) and isinstance(_p, int) and _b and not _p:
            return MISSING, ("EVERY measurable cell of the console is blank (%d of %d) - the window "
                             "is drawing nothing at all. The whole-window witness owns the rescue "
                             "for this; this row exists so it is never SILENT while that one is "
                             "deciding." % (_b, _b + _p))
        return OK, str(r.get("why") or "every measurable part of the window is drawn")
    return MISSING, ("the console is PARTLY DRAWN and its beat cannot see it: %s. This is the shape "
                     "he reported - the DOM intact, the rail painting, and a whole column empty. "
                     "The whole-window witness reads this as healthy by design."
                     % str(r.get("why"))[:220])


def _check_the_river_is_moving():
    """v2742 — 40 OF 40 REELS SIT AT A STATION NO AUTOMATIC LANE TAKES ITS INPUT FROM.

    Konyo: *"something needs to run that river ... something needs to automate this puppy if its
    not wired connect and wire it properly"*.

    MEASURED across his 40 reels: EMPTY 6 · STATION 7 · PRINTER 11 · JOIN 4 · CAPTURE 12.
    Two are by design. Two are real, and this row exists to keep them visible:
      · STATION (7, the PAID queue) HAS a reel-reading lane — chronicle_autoreel_tick — but it
        selects on the durable sweep memory rather than on this station, so the queue and the
        reader never meet.
      · PRINTER (11) owes a SEAL only the vault lane can write, and its work list is retention's
        `vault-owes` — measured 0 of 40 PERMANENTLY, because that tag is the LAST rule in a
        first-match-wins list and every reel matches something earlier. Eleven reels are waiting
        for a seal nothing will ever write.

    ⚠ THIS ROW IS RED TODAY AND THAT IS CORRECT. A check that could only ever be green measures
    nothing. It goes green when a lane actually drains a station, not when someone edits a list.
    ⚠ IT IS A STATE, NOT A LOCK. No wilson score belongs here: a score belongs on a claim that can
    be ATTACKED, and "the river is moving" is a reading. Inventing attacks to give a state a number
    is the inflation `_hardening_gap` refuses. [[build-the-heart-and-census-everywhere]]
    """
    try:
        import reel_router as _rr
        d = _rr.route()
    except Exception as e:
        return UNKNOWN, "reel_router will not answer (%s), so the river is UNMEASURED" % str(e)[:60]
    if not isinstance(d, dict) or not d.get("ok"):
        return UNKNOWN, ((d or {}).get("why") or "reel_router did not answer")
    rows = d.get("reels")
    if not isinstance(rows, list) or not rows:
        return UNKNOWN, "no reel was stationed, so nothing can be concluded about the river"
    stuck = {}
    for r in rows:
        # the list is guarded above; its ELEMENTS are not, and `(r or {}).get` raises on a truthy
        # non-dict exactly as it did in the two rows above
        if not isinstance(r, dict):
            continue
        st = r.get("station")
        if not st or st in _BY_DESIGN_STATIONS or st in ("ROUTED", "TOMBSTONE"):
            continue
        if r.get("owes"):
            stuck[st] = stuck.get(st, 0) + 1
    if not stuck:
        return OK, "every stationed reel has a lane that can take it (%d reel(s) walked)" % len(rows)
    total = sum(stuck.values())
    named = ", ".join("%s %d" % (k, v) for k, v in sorted(stuck.items(), key=lambda kv: -kv[1]))
    return MISSING, ("%d of %d reel(s) sit at a station that owes work no automatic lane delivers "
                     "(%s). They are not stuck on evidence — nothing is scheduled to move them."
                     % (total, len(rows), named))


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


def _check_his_progress_number_has_not_been_overwritten():
    """THE WATCHDOG HE ASKED FOR, and the fault it was built the morning of 2026-08-28 to catch.

    He opened the board and saw "0/0 ... some bug.. browser is wiped", then 117/135 sets and 266/403
    uniques against a real 120 and 280. Nothing was wiped: his ledger read foundLog 391, setPieces
    120, rwMade 99 all morning, and rendering that exact store on a clean board gives 120/135 and
    280/403. What went wrong was the BANKING — bible.html posts its counts to the console and the
    console wrote them into one global slot, so a second page in a different world overwrote his.
    board_tally.json carried route id 77f6..., his board's store is c5c2....

    His ask, verbatim: "this needs to get updated and locked going up like watchdog eagleeye should
    be updating the real count going up once every day atleast ... so when i log in now or this ever
    happens it saves from the 278/403 and the 120/135".

    So the tally is banked per world with a per-world high-water mark, and THIS is the surface that
    tells him when something falls. It reports, it does not heal: silently restoring the high number
    would hide the thing that made it fall, and a wrong number that looks right survives for weeks.
    [[feedback-silence-is-not-evidence]] [[unknown-stays-unknown]]
    """
    import json as _j
    fp = os.path.join(HERE, "board_tally.json")
    if not os.path.exists(fp):
        return UNKNOWN, ("no board tally has ever been banked — open the board once so it can "
                         "publish what it holds")
    try:
        with open(fp, encoding="utf-8") as fh:
            doc = _j.load(fh)
    except Exception as e:
        return MISSING, ("board_tally.json will not parse (%s) — his progress numbers are "
                         "UNREADABLE, which is not the same as zero" % str(e)[:50])
    if not isinstance(doc, dict):
        return MISSING, "board_tally.json is not an object"

    if doc.get("contested"):
        rows = doc["contested"]
        say = " vs ".join("%s sets=%s uniques=%s"
                          % (str(r.get("route") or "?").split("|")[0][:8],
                             r.get("sets"), r.get("uniques")) for r in rows[:3])
        # ⚠⚠ v2643 — THIS `return` USED TO SIT HERE AND IT BLINDED EVERYTHING BELOW IT.
        # The high-water/drop check further down — "his published progress is BELOW its own
        # high-water mark", the one that catches a ledger entry vanishing — was UNREACHABLE for
        # 7.8 days behind a contested alarm that was itself false (a week-stale row from a world
        # `ownerId` had already excluded). A warning is not a verdict, and a warning that returns
        # before a detector has silently switched that detector off.
        # It is carried in `notes` and reported WITH whatever the real check concludes.
        _contested_say = ("⚠ two worlds are both claiming to be him and they disagree: %s. The "
                          "newest is published, which may be the wrong one — open the board and "
                          "check the number before trusting anything downstream" % say)
    else:
        _contested_say = ""

    high = doc.get("high") if isinstance(doc.get("high"), dict) else {}
    drops = doc.get("drops") if isinstance(doc.get("drops"), list) else []
    # ⚠⚠ v2643 — PICK HIS WORLD BY `ownerId`, NOT BY DICT ORDER. This took the FIRST row whose
    # `who.pfx` is "" and stopped. Measured 2026-09-05: it happens to land on 77f641… , which IS
    # `ownerId` — but by luck of iteration order across 404 routes, not by a decision. `ownerId` is
    # resolved authoritatively upstream and sits right here in the doc; using anything else to
    # answer "whose high-water mark" is a guess wearing a measurement's clothes.
    _own = str(doc.get("ownerId") or "")
    key = ""
    for k, row in (doc.get("byRoute") or {}).items():
        w = row.get("who") or row.get("route") or {}
        if isinstance(w, dict) and _own and str(w.get("id") or "") == _own:
            key = k
            break
    if not key:
        for k, row in (doc.get("byRoute") or {}).items():
            w = row.get("who") or row.get("route") or {}
            if isinstance(w, dict) and w.get("pfx") == "":
                key = k
                break
    below = []
    for lane in ("sets", "uniques", "runewords"):
        now = (doc.get(lane) or {}).get("have")
        top = ((high.get(key) or {}).get(lane) or {}).get("have")
        if isinstance(now, int) and isinstance(top, int) and now < top:
            below.append("%s %d (best %d)" % (lane, now, top))
    if below:
        # ⚠⚠ v2643 — THE LAST DROP OF *HIS* WORLD, NOT THE LAST ROW IN THE FILE.
        # `drops[-1]` was literally a test fixture on his live store:
        #     {"route": "real-1|main", "lane": "runewords", "from": 42, "to": 0, "at": null}
        # so the first time his progress ever fell, this sentence would have reported a FIXTURE'S
        # fall as his — "the last recorded fall was runewords 42 -> 0", dated 1970 because `at` is
        # null. ⚠ THAT PATH WAS UNREACHABLE UNTIL THIS SAME VERSION UN-BLINDED IT: the contested
        # early-return above meant this branch never ran. Un-blinding a check makes everything it
        # says reachable, so what it says has to be true on the same day. [[sweep-dont-ask]]
        # ⚠ The fixture row is NOT removed — it is his file and nothing here prunes it; it is
        # simply no longer read as his.
        _mine = [d for d in drops if isinstance(d, dict) and (not key or d.get("route") == key)]
        recent = _mine[-1] if _mine else {}
        return MISSING, ("his published progress is BELOW its own high-water mark: %s. The last "
                         "recorded fall was %s %s -> %s. Nothing has been auto-restored, because "
                         "putting the number back would hide whatever took it away."
                         % ("; ".join(below), recent.get("lane") or "?",
                            recent.get("from"), recent.get("to")))
    if not high:
        return UNKNOWN, ("no high-water mark banked yet — it fills on the next tally the board "
                         "posts" + ((" · " + _contested_say) if _contested_say else ""))
    parts = []
    for lane in ("sets", "uniques", "runewords"):
        top = ((high.get(key) or {}).get(lane) or {}).get("have")
        if isinstance(top, int):
            parts.append("%s %d" % (lane, top))
    return OK, ("his progress is at its own best: %s — banked per world, so another browser cannot "
                "overwrite it" % (", ".join(parts) or "nothing banked yet"))


def _check_no_ledger_ENTRY_has_silently_vanished():
    """His 20-minute ledger snapshots are what made 2026-08-28 recoverable. Nothing SHOUTED.

    Overnight his bare d2r_foundLog went 391 -> 383 and d2r_setPieces 120 -> 117. The snapshots
    recorded every step of it and no surface said a word, so he found out by opening the board and
    asking "where is al my uniques and runeword and set items?". A record that captures a loss
    without reporting it is an autopsy, not a guard.

    THIS COMPARES THE TWO NEWEST SNAPSHOTS AND NAMES WHAT WENT. Names, not counts: "you are down 8"
    is not actionable and "Atma's Scarab, Gheed's Fortune, Frostburn ..." is. The names it printed
    that morning were the diagnosis — one carried a CURLY apostrophe and three were the exact
    entries d2r_setRepairKept is supposed to protect, which is what turned a mystery into a class.

    ⚠ IT NEVER RESTORES. Putting the entries back here would hide whatever removed them, and a
    ledger that heals itself silently is how a defect survives for months. It reports; the restore
    is a deliberate act through the board's own gated path. [[feedback-silence-is-not-evidence]]

    ⚠ AND A SHRINKING LEDGER IS NOT THE SAME AS A CHANGING ONE. Items ARRIVE constantly — 9 set
    pieces were registered in the very window 17 uniques vanished — so only REMOVALS are reported.
    """
    import glob as _glob
    import json as _j
    d = os.path.expanduser("~/d2r_ledger_backups")
    if not os.path.isdir(d):
        return UNKNOWN, ("no ledger snapshot directory — nothing to compare, so a loss would be "
                         "invisible. `python3 ~/d2r_ledger_backups/snapshot_ledger.py` starts it")
    files = sorted(_glob.glob(os.path.join(d, "ledger_*.json")))
    if len(files) < 2:
        return UNKNOWN, "fewer than two snapshots — there is nothing to compare against yet"

    def _load(p):
        try:
            with open(p, encoding="utf-8") as fh:
                doc = _j.load(fh)
        except Exception:
            return None
        led = doc.get("ledger") if isinstance(doc.get("ledger"), dict) else doc
        if not isinstance(led, dict):
            return None
        out = {}
        for k in ("foundLog", "setPieces", "rwMade", "owned"):
            v = led.get(k)
            if isinstance(v, dict):
                out[k] = set(v)
            elif isinstance(v, list):
                out[k] = {str(x) for x in v}
        return out or None

    new = _load(files[-1])
    old = _load(files[-2])
    if new is None or old is None:
        return UNKNOWN, ("a snapshot will not parse, so the comparison is UNKNOWN — which is not "
                         "the same as 'nothing was lost'")

    lost = {}
    for k in ("foundLog", "setPieces", "rwMade"):
        if k in new and k in old:
            gone = sorted(old[k] - new[k])
            if gone:
                lost[k] = gone
    if not lost:
        n = len(new.get("foundLog") or ())
        return OK, ("nothing has disappeared between the last two snapshots (%d found-ledger "
                    "entries, %d set pieces)" % (n, len(new.get("setPieces") or ())))

    parts = []
    for k, gone in lost.items():
        shown = ", ".join(gone[:6]) + (" +%d more" % (len(gone) - 6) if len(gone) > 6 else "")
        parts.append("%s lost %d: %s" % (k, len(gone), shown))
    return MISSING, ("ENTRIES DISAPPEARED between %s and %s — %s. Nothing has been put back: "
                     "restoring here would hide whatever removed them. To recover: "
                     "python3 ~/d2r_ledger_backups/restore_ledger.py --file %s --apply "
                     "(it goes through the board's own dated, merge-max, undoable apply)"
                     % (os.path.basename(files[-2]), os.path.basename(files[-1]),
                        " | ".join(parts), os.path.basename(files[-2])))


def _check_the_board_store_did_not_come_up_empty():
    """The event that cost him 17 uniques on 2026-08-28, made loud.

    His board's localStorage went empty overnight; the boot seed floor refilled it from the seeds
    compiled into bible.html, and the board came up reading a plausible 383/117. Nothing was
    reported. The rebuild is what hid the loss — a store that had lost EVERYTHING repainted itself
    into something that looked merely slightly behind.

    bible.html now writes d2r_storeEmptied when it seeds over a store that had clearly run before.
    This is the surface that reads it, because a flag nobody looks at is the same as no flag.
    """
    got = _board_read()
    if not got:
        return UNKNOWN, "the console did not answer — nobody asked, so nothing is known"
    if got.get("ok") is False:
        return UNKNOWN, "the board refused the read: %s" % str(got.get("why"))[:90]
    if not got.get("boardLoaded"):
        return UNKNOWN, ("the board is not loaded in the window, so its store cannot be asked — "
                         "which is not the same as 'it is fine'")
    if "storeEmptied" not in got:
        return UNKNOWN, ("this console predates the storeEmptied field (v2216) — restart it, or an "
                         "emptied store stays invisible here")
    ev = got.get("storeEmptied")
    if not ev:
        return OK, "the board's store has not come up empty"
    # ⚠⚠ v2991 — THIS SENTENCE DESCRIBED BEHAVIOUR v2988 REMOVED, AND IT IS THE ONE HE READS.
    # It said the store "was refilled from the built-in seeds". Since v2988 the floor REFUSES to
    # run over a store that became empty, so the board shows 0 — while this row told him it had
    # been refilled to a plausible 383/117. The eye put the cost plainly: "the operator is pointed
    # at 17 items missing from a full-looking store when the actual state is an obviously empty
    # board." Restore was still the right action; the diagnosis was the old one.
    # ⚠ The WRITER's two sentences were corrected in v2990 and this READER was not — a
    # caller/callee split where the contract changed and the surface describing it did not.
    # [[label-outlived-referent]] [[the-unjoined-end]]
    # ⚠⚠ v2993 — A RECOVERED STORE MUST STOP READING AS MISSING. The record had no exit: the
    # advertised restore (`restore_ledger.py --apply`, a merge-max chronicleApply) puts the NAMES
    # back and never removes `d2r_storeEmptied`, so this row reported MISSING for ever — including
    # after a successful recovery. A permanent alarm is one he learns to ignore, which is worse
    # than no alarm at all. bible.html now stamps `recoveredAt` when the store has contents again,
    # and keeps the record as history rather than deleting his evidence.
    _rec = ev.get("recoveredAt") if isinstance(ev, dict) else None
    if isinstance(_rec, (int, float)) and _rec > 0:
        import datetime as _dt2
        # ⚠ v3005 — THE COUNTS RIDE WITH THE CLAIM. Eye finding 3: `recoveredAt` means "a ledger
        # key exists", which one hand-added name satisfies — so "no longer needs action" could
        # stand over a store holding 1 of 20 lost items. The magnitude is what lets HIM judge
        # whether the recovery is real; a claim without its number cannot be argued with.
        # [[zero-needs-a-denominator]]
        _c2 = got.get("counts") if isinstance(got.get("counts"), dict) else {}
        return OK, ("the board's store came up empty once and has contents again since %s UTC — "
                    "now %s foundLog / %s setPieces. The record is kept as history — it is what "
                    "says which backup predates the loss. Judge the counts, not the flag: one "
                    "recovered name stamps it just as fully as four hundred."
                    % (_dt2.datetime.utcfromtimestamp(_rec / 1000.0).strftime("%Y-%m-%d %H:%M"),
                       _said(_c2.get("foundLog")), _said(_c2.get("setPieces"))))
    # ⚠⚠ v3004 — THE ADVERTISED RESTORE COULD NOT CLEAR THE ALARM UNTIL A RELOAD. Found by the
    # cross-family eye on v2993: `restore_ledger.py --apply` writes names through chronicleApply
    # into the ALREADY-LOADED board, while `recoveredAt` is stamped only in bible.html's load-time
    # block — so he runs the exact command the MISSING row prints, the store genuinely refills,
    # and this row keeps saying MISSING and keeps telling him to run it again for the rest of the
    # session. The original bug was "forever, across boots"; v2993 made it "until the document
    # reloads", which --apply does not do. The evidence was in hand the whole time: _board_read()
    # already carries counts (measured live: foundLog=440 / setPieces=129 beside the event).
    # ⚠ My first draft of this comment claimed the LIVE event was still open — it was not: an
    # 80-char print truncation had hidden its recoveredAt, stamped at the 08:11 board reload. The
    # counts path below is therefore verified by STUB (an open event beside non-zero counts), not
    # by the live board, and saying otherwise would be a probe artifact wearing a measurement's
    # clothes. [[source-window-shortcut]] [[inherited-claim-is-not-evidence]]
    # ⚠ Only a MEASURED count exits; absent counts fall through, because "could not count" must
    # never read as "has contents". [[the-unjoined-end]] [[unknown-stays-unknown]]
    _cnt = got.get("counts") if isinstance(got.get("counts"), dict) else {}
    _fl, _sp = _cnt.get("foundLog"), _cnt.get("setPieces")
    if ((isinstance(_fl, (int, float)) and _fl > 0)
            or (isinstance(_sp, (int, float)) and _sp > 0)):
        return OK, ("the board's store came up empty once and HOLDS CONTENTS AGAIN — measured "
                    "this read: %s foundLog / %s setPieces. The episode is not closed yet "
                    "(recoveredAt stamps at board load, and this board has not reloaded since "
                    "the names came back), so the record stays as history and the next board "
                    "load closes it. No action needed."
                    % (_said(_fl), _said(_sp)))
    _at = ev.get("at") if isinstance(ev, dict) else None
    _boots = ev.get("boots") if isinstance(ev, dict) else None
    _when = ""
    if isinstance(_at, (int, float)) and _at > 0:
        import datetime as _dt
        _when = (" First seen %s UTC"
                 % _dt.datetime.utcfromtimestamp(_at / 1000.0).strftime("%Y-%m-%d %H:%M"))
        if isinstance(_boots, int) and _boots > 1:
            _when += " and still empty %d boots later" % _boots
        _when += "."
    return MISSING, ("THE BOARD'S STORE CAME UP EMPTY — it lost its contents on a load that had "
                     "run before. The seed floor is REFUSING to run over it, so the store stays "
                     "EMPTY rather than being papered over with defaults: an empty store you can "
                     "see is recoverable, a seeded one is not.%s That is how 17 uniques and 3 set "
                     "pieces went missing on 2026-08-28 while the board still read a plausible "
                     "383/117. Recover with: "
                     "python3 ~/d2r_ledger_backups/restore_ledger.py --apply" % _when)


def _check_the_shadow_gate_is_learning():
    """The Wilson lane, in the console. Konyo: "make it self improving and really accurate so its
    locked and locks in the console."

    It accumulates on every sweep through apply_proposal — the one door every proposal passes — so
    its sample is not a function of which call sites someone remembered to wire. This is where the
    record becomes visible, because a lane that only answers when asked by hand is a lane nobody
    asks.

    ⚠ IT NEVER PROMOTES ITSELF, and this check never recommends that it should. Reaching the
    threshold means the record is worth reading. A gate that switched on its own agreement
    statistics would be marking its own homework, and the failure lands as a wrong verdict written
    into his grail — the one place a wrong answer is invisible.
    """
    try:
        sys.path.insert(0, HERE)
        import shadow_ledger as _sl
        st = _sl.state()
    except Exception as e:
        return UNKNOWN, "the shadow lane could not be asked: %s" % str(e)[:90]
    if not st.get("ok"):
        return MISSING, st.get("say") or "the shadow ledger is unreadable"
    state = st.get("state")
    if state == "empty":
        return UNKNOWN, st.get("say")
    if state == "disagrees":
        return MISSING, st.get("say")
    # thin and agrees are both OK — one of them is just younger
    return OK, st.get("say")


def _check_the_tooltip_finder_is_honest():
    """v2321 — is the tooltip finder locating tooltips, or the HUD?

    Text density alone returns the same top-right corner box on every unhovered frame — measured,
    five in a row on a reel that registered nothing. The 8% area floor separates his real tooltip
    (33.4% of the frame) from that impostor (2.8%). This reports whether the floor is still doing
    its job and what the located tooltips actually yielded.
    """
    try:
        import tooltip_find as tf
    except Exception as e:
        return MISSING, "the tooltip finder will not import: %s" % str(e)[:70]
    try:
        r = tf.report()
    except Exception as e:
        return MISSING, "its ledger could not be read: %s" % str(e)[:70]
    if not r.get("attempts"):
        return MISSING, ("the finder has never been asked — no frame has been put through it, so "
                         "nothing is known about it either way")
    if r.get("judged"):
        return OK, r["say"]
    return MISSING, ("%d located, %d refused, but none judged yet — nobody has said whether a "
                     "located tooltip yielded a name" % (r.get("located") or 0, r.get("refused") or 0))


def _check_his_gear_is_being_learned():
    """v2320 — is the main-character ledger actually accumulating, or silently empty?

    The LANE rule protects the equipment panel while it is on screen. This ledger is what protects
    the same item in a frame that only shows the stash — and it is only worth anything if sightings
    are reaching it. An empty ledger after a session of farming is a lane that is not being fed,
    which looks exactly like a lane with nothing to say.
    """
    try:
        import main_character as mc
    except Exception as e:
        return MISSING, "the main-character ledger will not import: %s" % str(e)[:70]
    try:
        r = mc.report()
    except Exception as e:
        return MISSING, "the ledger could not be read: %s" % str(e)[:70]
    tracked, locked = int(r.get("tracked") or 0), len(r.get("locked") or [])
    if tracked == 0:
        return MISSING, ("nothing has been recorded yet — no sighting has reached the ledger, so "
                         "no item can earn a lock. That is UNKNOWN, not 'he owns nothing'.")
    # ⚠ "0 locked" HAD TWO MEANINGS AND THIS RAIL REPORTED BOTH AS OK. One is "no item has
    # cleared the floor yet", which more farming fixes. The other is "no item can ever clear it",
    # which no amount of farming fixes — and that was the true one: `equip` only increments for
    # lane "equipment", and reel_segments has no such activity, so the input is pinned at zero.
    # Measured on his ledger: 4 tracked, every row equip:0, reported OK. [[label-outlived-referent]]
    if r.get("blockedWhy"):
        return MISSING, ("%d item(s) tracked and NOTHING CAN LOCK — %s"
                         % (tracked, r["blockedWhy"]))
    return OK, ("%d item(s) tracked, %d locked as his gear (floor %.2f, %d-look minimum, "
                "%d equipment sighting(s))"
                % (tracked, locked, r.get("floor") or 0.0, r.get("minSightings") or 0,
                   r.get("equipSightings") or 0))


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
    # ⚠⚠ v2771 — THIS ROW WAS CRYING WOLF ABOUT HIS OWN RULING, and a distrusted instrument is a
    # switched-off one. It required the throw bar to be strictly above the keep bar ON WITNESSES,
    # and reported MISSING when he levelled them on 2026-09-07:
    #   *"make it two also.. its fine.. i will review what i throw regardless.. as long as it in
    #    that bin"* · *"i will decide if to throw it out or not to"*
    # The DANGER the row exists for is real and unchanged — there is no un-throw in Diablo — but
    # the protection is not carried by the witness count alone. Throwing still demands STRICTLY
    # more CONFIDENCE (0.85 vs 0.55), and `witness_field="session"` makes the throw bar count
    # independent RECORDINGS where the keep bar counts looks. So the bars are still ordered; they
    # are ordered on a different axis than this row was checking.
    # ⇒ The invariant is now "strictly above on AT LEAST ONE axis, and never below on either".
    #   A true inversion — throw becoming EASIER than keep — still goes red.
    _tw = getattr(vr, "THROWOUT_MIN_WITNESSES", 0)
    _kw = getattr(vr, "KEEP_MIN_WITNESSES", 0)
    _tc = getattr(vr, "THROWOUT_CONF_FLOOR", 0.0)
    _kc = getattr(vr, "KEEP_CONF_FLOOR", 0.0)
    if _tw < _kw or _tc < _kc:
        return MISSING, ("THE THROW BAR IS NOW EASIER THAN THE KEEP BAR — witnesses %s vs %s, "
                         "confidence %.2f vs %.2f. An item could be thrown on evidence that would "
                         "not have kept it, and there is no un-throw in Diablo."
                         % (_tw, _kw, _tc, _kc))
    if _tw == _kw and _tc == _kc:
        return MISSING, ("the throw bar and the keep bar are IDENTICAL on both axes (%s witnesses, "
                         "%.2f confidence) — nothing anywhere makes throwing harder than keeping, "
                         "and there is no un-throw in Diablo" % (_tw, _tc))
    return OK, ("%s locked; keep needs %d look(s) at conf %.2f, throw needs %d recording(s) at "
                "conf %.2f — throw is stricter on %s"
                % (" + ".join(locked), _kw, _kc, _tw, _tc,
                   "witnesses and confidence" if (_tw > _kw and _tc > _kc)
                   else ("witnesses" if _tw > _kw else "confidence")))


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


# v2183 — several times one honest pass (8 names x 18 frames = 144 reads, measured on his log),
# and far below the 3,434 total the runaway reached. Asserted from BOTH sides by
# TestV2182TheHuntEyeMeasuresTHISRunNotEver so it can never become a threshold above its own
# signal. [[feedback-threshold-above-the-ceiling]]
_ONE_PASS_IS_ABSURD = 600


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
    # ⚠ v2182 — MEASURE **THIS RUN**, NOT THE WHOLE TAIL.
    # The 2MB tail spans hours and many process lifetimes. Right after the v2176 fix landed and
    # his console was relaunched onto it, this still reported "paying 2,149 reads per new
    # sighting" — TRUE of the log, FALSE of the running build, because the runaway it measured had
    # happened before the relaunch. A reading carries the age of the thing it measured, not of the
    # fetch. And a check that stays red after the repair becomes furniture, which is the same
    # defect as one that is always green. [[stale-reading]]
    # ⚠ v2183 — ANCHOR THE MARKER. A plain substring search for "CONSOLE BOOT " is matched by
    # ITEM NAMES: this log carries names an AI read off his game screenshots, and a review pointed
    # out that one containing that text would move the slice past every real hunt line and report
    # a live runaway as "no hunt has run". The check's OWN failure prose names the marker too, so
    # a log that ever quoted it would blind the check permanently. Require the whole shape at the
    # start of a line: the emoji, a version, and a pid. [[source-reading-guard]]
    _boots = [m.start() for m in _re.finditer(
        "(?m)^\\s*\\U0001f680 CONSOLE BOOT \\S+ pid=\\d+", txt)]
    _window = "since this console booted"
    if _boots:
        txt = txt[_boots[-1]:]
    else:
        # No marker in the tail: either an older build is running, or the tail is long enough that
        # the boot scrolled out. Either way the window is UNKNOWN and must be named as such rather
        # than quietly presented as current. [[unknown-stays-unknown]]
        _window = ("across a log window of unknown age — no CONSOLE BOOT marker in the tail, so "
                   "this may include runs from before a fix")
    # ⚠ v2183 — AND SO MUST THE PASS LINES BE ANCHORED, for the same reason. Unanchored, a single
    # OCR'd line quoting the phrase counted as a second pass, and TWO passes with no sightings is
    # exactly the trigger — so one honest miss plus one unlucky item name read as the runaway.
    # The real line is `   🔎 [uniques] hunt done: N read(s), new sightings for M name(s)`.
    passes = _re.findall(
        "(?m)^\\s*\\U0001f50e \\[(?:uniques|sets)\\] hunt done: (\\d+) read\\(s\\), "
        "new sightings for (\\d+) name", txt)
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
        return "ok", "no hunt has run %s — nothing is being bought" % _window
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
    # ⚠ v2183 — A SPEND THIS CHECK CANNOT ATTRIBUTE TO THE RUNNING BUILD IS UNKNOWN, NOT MISSING.
    # Without a boot marker the window may be entirely pre-fix — which is precisely the reading
    # that made this check wrong on his machine. Saying "missing" then is the stale verdict again,
    # wearing more words. [[stale-reading]] [[unknown-stays-unknown]]
    _verdict = "missing" if _boots else "unknown"

    # ⚠ v2183 — AND ONE PASS IS A MISS ONLY AT A SANE PRICE. The review found that a single pass
    # of any size returned "ok": `hunt done: 3434 read(s), new sightings for 0 name` was a miss,
    # not a loop. One honest pass is 8 names x 18 frames = 144 reads (measured). A single pass
    # costing several times that and bringing nothing home is not a miss, whatever the pass count.
    if sightings == 0 and len(passes) == 1 and reads >= _ONE_PASS_IS_ABSURD:
        return _verdict, ("a single hunt pass spent %d PAID reads %s and found NOTHING. One honest "
                          "pass is about 144 reads (8 names x 18 frames), so this is not a miss — "
                          "something is searching far more film than the cap should allow."
                          % (reads, _window))
    if sightings == 0 and len(passes) >= 2:
        return _verdict, ("the hunt has run %d pass(es) for %d PAID read(s) %s and found "
                           "NOTHING. That is the v2174 loop: it is re-buying names that already "
                           "came back empty. Check the hunt memory is being written "
                           "(tv/chron_hunt_memory.json, or beside chronicle_swept.json under "
                           "TV_HIST)." % (len(passes), reads, _window))
    # ⚠ NOT `and reads < 200`. A single pass with sightings==0 falls past every branch below and
    # reaches the `%.0f` tail with per=None, which raises inside a health check — the doctor
    # reporting an exception instead of a verdict. One pass is a miss at ANY price.
    if len(passes) < 2:
        return "ok", ("%d hunt pass(es), %d paid read(s), %d sighting(s) %s — a single pass is "
                      "a miss, not a loop" % (len(passes), reads, sightings, _window))
    per = reads / float(sightings) if sightings else None
    if per and per > 400:
        return _verdict, ("the hunt is paying %.0f reads per new sighting (%d reads, %d "
                           "sighting(s)) %s. The empty-hunt memory is not holding — a name that "
                           "found nothing is being bought again."
                           % (per, reads, sightings, _window))
    return "ok", ("the hunt is paying %.0f read(s) per new sighting across %d pass(es) %s"
                  % (per, len(passes), _window))


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
    # v2221 — NAME THE RETAINED ENTRIES. chronicle_swept.json holds MORE entries than there are
    # reels on disk (36 vs 30, measured 2026-08-28) and nothing said why, so the file read as a
    # record that disagrees with the disk — which is what #167 was reopened on, and what nearly got
    # them "cleaned". They are reads whose footage was later pruned: pages 22/35/21/22/22/140, the
    # extract-then-prune loop working. An unexplained true number invites a destructive fix.
    try:
        _sp = ca._chron_swept_split(mem, dirs)
        _ret = ("" if not _sp.get("retained") else
                " · %d more entr%s retained for footage since pruned (the read is the record)"
                % (_sp["retained"], "y" if _sp["retained"] == 1 else "ies"))
    except Exception:
        _ret = ""
    # ⚠ v2225 — _ret rides on EVERY return below, not only the clean one. The first cut appended it
    # to the OK path alone, so the moment any reel owed a read the explanation for the 36-vs-30 gap
    # vanished — exactly when he is most likely to be reading the line and most likely to conclude
    # the record disagrees with the disk. An explanation that disappears under load is not one.
    if not owed:
        return OK, "all %d reel(s) have been read%s%s" % (len(dirs), tail, _ret)

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
                         % (len(owed), len(dirs), hours, tail + _ret))
    return OK, ("%d reel(s) owe a read, last banked %.1fh ago — the loop is working through them%s"
                % (len(owed), hours, tail + _ret))


def _check_the_vault_proposal_still_clears_todays_bar():
    """★ THE STORED VAULT PROPOSAL, RE-GATED AGAINST TODAY'S BARS.

    Konyo, 2026-09-07: *"the vault accumalator that should be connected to the heart of the console
    with the vault and joined obivously too"* and *"just make sure its all wired and not stale and
    connected to the heart.. we soon will hit the VAULT and start debugging that"*.

    ⚠⚠ WHY A ROW AND NOT A FIX. A proposal is a PHOTOGRAPH of a decision made under the bars that
    existed when it was taken. The bars can move afterwards, and then the panel shows rows labelled
    OWNED that today's own rule would not accept — a stale display over a correct gate. Nothing
    watched that: `console_doctor` had exactly one vault row (`vault stores`, which asks only
    whether the files are READABLE), and the proposal itself was supervised by nothing.

    ⚠ AND THE DRIFT IS REAL AND HAS ALREADY HAPPENED IN BOTH DIRECTIONS. When this task was
    written the bar was 3 and 6 of his 7 stored rows failed it. Re-measured when it came to be
    built: `KEEP_MIN_WITNESSES` is 2 again ("HIS RULING, 2026-09-07") and all 7 pass. The task's
    own premise had expired — which is exactly the argument FOR this row rather than against it.
    A number I measured once is not evidence later. [[inherited-claim-is-not-evidence]]

    ⚠ IT NEVER RE-GRADES HIS STORED ROWS, and it never touches the bar. The write path already
    re-gates at the WRITE (`vault_apply`, v1595) and is ALL-OR-NOTHING, so a stale proposal cannot
    land badly — pressing register would REFUSE ALL SEVEN rather than write six wrong ones. What
    was missing was only that nobody was told. This says the delta out loud and stops there.
    ⛔ Lowering KEEP_MIN_WITNESSES to make stored rows pass would be repairing the bar to fit the
    data. The bar guards a deleter.
    """
    try:
        import vault_retro as _vr
    except Exception as e:
        return UNKNOWN, "vault_retro will not import (%s), so the proposal is ungraded" % str(e)[:60]
    import io as _io
    import json as _json
    import os as _os
    # ⚠⚠ THE PATH AUTHORITY, NOT A SECOND JOIN. Found by the post-ship review: this hardcoded
    # os.path.join(HERE, ...) while control_app resolves the ledger through TV_VAULT_LEDGER /
    # _fixture_root_for_state(). With either set, the row graded a file the register button would
    # never write — and a gate run reached into his REAL 7-row ledger instead of the fixture.
    # The comment above control_app's own definition says it outright: "Guard the PATH, not the
    # call site." [[feedback-fixtures-never-touch-live-data]]
    p = None
    try:
        import control_app as _ca
        p = getattr(_ca, "VAULT_LEDGER_PATH", None)
    except Exception:
        p = None
    if not p:
        p = _os.environ.get("TV_VAULT_LEDGER") or _os.path.join(HERE, "vault_accum.json")
    if not _os.path.isfile(p):
        # ⚠ NO STORE IS NOT A CLEAN BILL AND NOT A FAULT. Nothing has been accumulated yet.
        # ⚠⚠ AND IT NAMES THE PATH IT LOOKED AT. Raised by the second eye: the control_app import
        # above is wrapped in a bare except, so a broken import silently falls back to a DIFFERENT
        # path — which is exactly the bug this row was just fixed for. "Nothing is stored" and
        # "I looked in the wrong place" produce the same sentence unless the place is in it.
        return OK, ("no vault proposal is stored at %s, so there is nothing whose grading could "
                    "have drifted — an empty queue, not a measured agreement" % p)
    try:
        d = _json.load(_io.open(p, encoding="utf-8"))
    except Exception as e:
        return UNKNOWN, ("vault_accum.json could not be read (%s), so whether its rows still "
                         "clear today's bar is UNKNOWN — it is NOT 'they do'" % str(e)[:60])
    rows = (d.get("result") or {}).get("owned") if isinstance(d.get("result"), dict) else d.get("owned")
    rows = [r for r in (rows or []) if isinstance(r, dict)]
    if not rows:
        return OK, ("the stored proposal holds no OWNED rows, so nothing is being offered for "
                    "registration — an empty proposal, not a disagreement")
    bad = []
    for r in rows:
        try:
            # ⚠ gate() TAKES THE SIGHTING LIST, NOT THE ROW, and its verdict key is "pass", not
            # "ok". My first cut passed the row dict: iterating a dict yields its KEYS, so `ev`
            # filtered to [] and every row came back "no evidence at all" — a confident 0 of 7 that
            # was purely an instrument failure. The suspiciously clean number was the tell.
            # [[feedback-suspect-the-instrument]]
            # ⚠⚠ THE BARS ARE PASSED EXPLICITLY, and that is not decoration. `gate()`
            # declares them as DEFAULT ARGUMENTS (min_witnesses=KEEP_MIN_WITNESSES), and
            # Python binds a default ONCE at def time — so calling gate() bare grades
            # against the bar as it was when the module was imported, while the sentence
            # below quotes `_vr.KEEP_MIN_WITNESSES` as it is NOW. Those can differ, and a
            # row whose verdict and whose stated bar disagree is worse than no row.
            # Found by the gate for this file failing: the simulated bar move did not
            # reach the comparison at all. [[label-outlived-referent]]
            g = _vr.gate(r.get("witnesses") or [],
                         conf_floor=_vr.KEEP_CONF_FLOOR,
                         min_witnesses=_vr.KEEP_MIN_WITNESSES)
        except Exception as e:
            return UNKNOWN, ("the vault gate raised %s while re-grading the stored proposal, so "
                             "the comparison is unmeasured" % type(e).__name__)
        if not g.get("pass"):
            bad.append((r.get("name") or "?", g.get("why") or ""))
    n = len(rows)
    if not bad:
        return OK, ("all %d stored OWNED row(s) still clear today's bar (conf %.2f, %d witnesses) "
                    "— the proposal on screen and the rule that would accept it agree"
                    % (n, _vr.KEEP_CONF_FLOOR, _vr.KEEP_MIN_WITNESSES))
    return MISSING, ("%d of %d stored OWNED row(s) NO LONGER clear today's bar (conf %.2f, %d "
                     "witnesses) — the panel labels them corroborated and the current rule calls "
                     "them unsure, so the register button offers a write that would be REFUSED in "
                     "full. First: %s — %s"
                     % (len(bad), n, _vr.KEEP_CONF_FLOOR, _vr.KEEP_MIN_WITNESSES,
                        bad[0][0], bad[0][1][:110]))


def _check_the_river_has_an_outlet():
    """★ THE RIVER COULD NOT FINISH A REEL, AND THE STATION THAT SAYS SO READ 0 FOR ITS WHOLE LIFE.

    Konyo's architecture: *"it just flows and eats session reels regardless of the route it come
    from initially… it just gets spit out properly"*, and *"there is no loop or worry because it
    gets eventually tombstoned and deleted and wiped completely. only the data and information gets
    extracted before hand."*

    `river_walk.py` recorded the weld in its own note: the ONLY writer of a tombstone row lives
    inside the deleter (`reel_retention.apply_plan` -> `_tombstone`), so a reel could not be
    recorded as CLOSED OUT without being REMOVED — and removal is behind the arming lock, which is
    False and stays False. Being finished and being deleted were one event. Measured on his shelf
    at the time: 40 reels, ROUTED 0, TOMBSTONE 0.

    ⚠ THIS ROW REPORTS FLOW, NOT REACHABILITY. Whether ROUTED can be reached at all is a structural
    fact and belongs in a gate, where it can be proven red — `test_the_river_has_an_outlet.py` does
    that. A doctor row that tried to assert reachability from live counts would grade a quiet shelf
    as a broken outlet every time nothing happened to qualify.

    ⚠⚠ IT ALWAYS PUBLISHES THE DECLINED COUNT. 12 of his reels sit at CAPTURE, which owes
    "CAPTURE, then ROUTE" — they cannot be closed out and never will be by a lane. Reporting only
    the routable number would say "0 waiting" on a shelf where 12 reels are permanently stuck, and
    that reads as done. [[zero-needs-a-denominator]]
    """
    try:
        import reel_router as _rr
    except Exception as e:
        return UNKNOWN, "reel_router will not import (%s), so the outlet is unmeasured" % str(e)[:60]
    try:
        rep = _rr.route()
    except Exception as e:
        return UNKNOWN, "the router raised (%s) — unmeasured, not clean" % str(e)[:60]
    if not rep.get("ok"):
        return UNKNOWN, ("the router did not answer (%s), so nothing here was measured"
                         % str(rep.get("why") or "no reason given")[:80])
    # ⚠ A STAMP STORE THAT COULD NOT BE READ MAKES ROUTED 0 A GUESS, NOT A COUNT. `route()`
    # publishes `outletReadable` precisely so this row does not have to infer it from a zero.
    if not rep.get("outletReadable", False):
        return UNKNOWN, ("the stamp store could not be read, so how many reels have been closed "
                         "out is UNKNOWN and specifically not zero — %s"
                         % str(rep.get("outletWhy") or "")[:90])
    counts = rep.get("counts") or {}
    routed = int(counts.get("ROUTED") or 0)
    shelf = int(rep.get("shelf") or 0)
    try:
        import reel_route_lane as _lane
        p = _lane.plan(rep)
    except Exception as e:
        return UNKNOWN, ("the route lane will not import (%s), so who is waiting to be closed out "
                         "is unmeasured" % str(e)[:60])
    if not p.get("ok"):
        return UNKNOWN, ("the route lane could not plan (%s)" % str(p.get("why") or "")[:80])
    waiting = len(p.get("route") or [])
    declined = len(p.get("declined") or [])
    # ⚠ v3020 — was "(REG-340)", which cites the CHARACTER-name ruling at an ITEM-name problem.
    tail = (" · %d at CAPTURE owe a capture change first — hover coverage, so the tooltips that "
            "carry item names are filmed — and no lane can move them" % declined) if declined else ""
    # ⚠⚠ v2770 — ASK THE DRIVER, NOT ONLY THE QUEUE. Until v2770 nothing CALLED the lane, so this
    # row could only ever say "they have not been closed out" without being able to say WHY — and
    # the answer was "because no code anywhere runs it". Now the triage tick drives it, and a
    # waiting queue means something different depending on whether the driver is alive:
    #   driver never ran   -> the loop is dead or the wiring broke. That is the finding.
    #   driver ran recently-> the reels arrived since, and the next tick will take them.
    # Collapsing those two into one sentence is how a dead loop reads as a busy one.
    drv = None
    try:
        import control_app as _ca2
        drv = getattr(_ca2, "_ROUTE_LANE", None)
    except Exception:
        drv = None
    drv_at = (drv or {}).get("at")
    drv_runs = int((drv or {}).get("runs") or 0)
    if waiting and not drv_runs:
        return MISSING, ("%d of %d reel(s) can be closed out RIGHT NOW and have not been, and the "
                         "route lane HAS NEVER RUN in this process — nothing is driving the "
                         "river. ROUTED holds %d%s" % (waiting, shelf, routed, tail))
    if waiting:
        import time as _t
        age = int(_t.time() - float(drv_at)) if drv_at else None
        return MISSING, ("%d of %d reel(s) are waiting to be closed out; the route lane last ran "
                         "%s and reported: %s. ROUTED holds %d%s"
                         % (waiting, shelf,
                            ("%ds ago" % age) if age is not None else "at an unrecorded time",
                            str((drv or {}).get("why") or "nothing"), routed, tail))
    if routed:
        return OK, ("%d of %d reel(s) closed out and none waiting — the river has an outlet and "
                    "it is being used%s" % (routed, shelf, tail))
    return OK, ("nothing currently qualifies to be closed out: no reel is at a station that owes a "
                "route outright%s. The outlet is reachable (proven in the gate), it simply has "
                "nothing to carry" % tail)


def _check_the_river_joints_carry():
    """★ v2761 — THE RIVER'S OWN DIAGNOSIS REACHES A SCREEN FOR THE FIRST TIME.

    Konyo: *"fix the gaps. connect it all to the heart of the console"*.

    MEASURED before writing this: `tv/river.py` measures all ELEVEN joints of the pipeline, names
    the first blockage in a sentence, and is imported by EXACTLY ONE FILE — its own test.
    `grep -rl 'import river' tv/*.py` -> test_the_river_carries_a_stamp.py. Neither corroborate.py
    nor console_doctor.py has ever asked it anything.

    ⚠ AND THERE IS ALREADY A ROW CALLED "the river" — it reads `reel_router` and answers WHERE
    REELS ARE STATIONED. That is a different question from WHETHER THE JOINTS CARRY. The console
    watched position and was blind to flow, and the two look similar enough that the gap survived.
    A sentence like "blocked at 'surface' — 0 of 14,034 sightings carry one" has never been on a
    screen he looks at. [[the-unjoined-end]] [[plumbing-with-no-tap]]

    ⚠ DRY IS NOT AUTOMATICALLY A FAILURE, and this must not cry wolf. Some joints are dry because
    the work genuinely has not been done and he can act; `gate` was dry because nothing NEW was
    proposed. So the row reports the CENSUS and names the first blockage, and grades on whether
    the river's own first-blockage sentence exists — never on a bare count.
    """
    try:
        import river as _rv
    except Exception as e:
        return UNKNOWN, "river.py will not import (%s), so no joint could be measured" % str(e)[:60]
    # ⚠ river.py's API is trace() + summary(rows) — NOT survey()/run(). My first cut guessed those
    # two names behind a hasattr, so the check would have returned UNKNOWN for ever while looking
    # like a wired watcher. Caught by grepping the module instead of trusting the guess.
    # [[feedback-suspect-the-instrument]]
    try:
        joints = _rv.trace()
        rep = _rv.summary(joints)
    except Exception as e:
        return UNKNOWN, "the river survey raised (%s) — unmeasured, not clean" % str(e)[:60]
    if not joints or not isinstance(rep, dict):
        return UNKNOWN, "the river reported no joints at all, so nothing here was measured"
    by = {}
    for j in joints:
        by[str(j.get("state"))] = by.get(str(j.get("state")), 0) + 1
    n = len(joints)
    dry = by.get("DRY", 0)
    unk = by.get("UNKNOWN", 0)
    say = str(rep.get("say") or "").strip()
    first = rep.get("firstBlockage")
    if dry:
        return MISSING, ("%d of %d joint(s) DRY%s — %s"
                         % (dry, n, (", %d unmeasured" % unk) if unk else "",
                            say or ("first blockage: %s" % first)))
    if unk:
        return UNKNOWN, "%d of %d joint(s) could not be measured" % (unk, n)
    return OK, "all %d river joint(s) carry" % n


def _check_the_console_UI_has_not_faulted():
    """Has the console reported a fault about ITSELF recently?

    ⚠ v2228 — THE EAGLE COULD NOT SEE THE SCREEN, so a display-side failure was invisible to every
    check here. He found the black-screen stage himself, twice, and reported it with screenshots
    while nothing in the tree knew anything was wrong. His instruction: "watch dog it and eagle
    eye it."

    The console now POSTs /api/ui_fault when it heals itself, and this reads that record. A fault
    that healed is still a fault — the point is that it stops being HIS job to notice.
    """
    try:
        import control_app as ca
        rows, why = ca.ui_faults_recent(24)
    except Exception as e:
        return UNKNOWN, "the fault log could not be read: %s" % str(e)[:80]
    if rows is None:
        return UNKNOWN, why or "the fault log is unreadable — which is not the same as no faults"
    if not rows:
        return OK, "the console has reported no fault about itself in 24h"
    import collections
    by = collections.Counter(r.get("kind") for r in rows)
    top = ", ".join("%s x%d" % (k, n) for k, n in by.most_common(3))
    newest = rows[-1]
    return MISSING, ("the console healed itself from %d fault(s) in 24h (%s) — most recently: %s. "
                     "It recovered, but this is the class he had to report by hand."
                     % (len(rows), top, str(newest.get("why"))[:110]))



def _check_no_panel_is_dark_with_its_content_in_hand():
    """A panel that HAS rows and is not on screen — the failure a green suite cannot see.

    WHY THIS IS A DOCTOR CHECK AND NOT ONLY A TEST. Konyo reported it twice: "daily tasks and
    chronicle tallys are not rendering here in this section", then "black space but image
    tooltips are still rendering". Both sightings were real and BOTH TIMES THE DATA WAS FINE.
    The roster was built, the tooltip drawn from the same rows worked, and the panel holding
    them carried a stale `hidden` attribute because the repaint memo returned before the
    un-hide. Every DOM-text assertion passed, because the text existed — it was never painted.

    So the honest place to catch it is the running page, which the UI heartbeat already is. The
    page classifies each panel itself (empty / shown / DARK) and this reads that verdict back.

    ⚠ THREE OUTCOMES, NEVER TWO. A console that has never beaten is UNKNOWN, not healthy — the
    same rule ui_beat_age() states about its own None. And a console older than v2336 reports no
    panels at all, which is also UNKNOWN and must never read as "all clear".
    [[unknown-stays-unknown]] [[regression-guard]]
    """
    st = _get("/api/status") or {}
    ub = st.get("uiBeat") if isinstance(st.get("uiBeat"), dict) else None
    if not ub:
        return UNKNOWN, "the console did not report a heartbeat, so nothing is known about his screen"
    if not ub.get("n"):
        return UNKNOWN, "no console has ever checked in — that is a headless run, not a healthy screen"
    panels = ub.get("panels")
    if not isinstance(panels, dict) or not panels:
        return UNKNOWN, ("this console is older than v2336 and does not report its panels — "
                         "unknown, not clear")
    dark = sorted([k for k, v in panels.items() if v == "DARK"])
    if dark:
        return MISSING, ("%s built its rows and is NOT on screen — the panel is dark with its "
                         "content in hand, which is the class he had to report by hand twice "
                         "(REG-415)" % ", ".join(dark))
    shown = sorted([k for k, v in panels.items() if v == "shown"])
    empty = sorted([k for k, v in panels.items() if v == "empty"])
    return OK, ("every panel holding content is on screen (%d shown%s%s)"
                % (len(shown), (": " + ", ".join(shown)) if shown else "",
                   ("; %d legitimately empty" % len(empty)) if empty else ""))



# `playwright test` reached the way a script actually invokes it. `playwright install` and any
# sentence merely NAMING playwright must not match — see browser_suites_among.
_RUNS_A_BROWSER_SUITE = re.compile(
    r"(?:npx\s+|yarn\s+|pnpm\s+|bunx\s+|node_modules/\.bin/|bin/)playwright\s+test\b")


def browser_suites_among(labels, agents_dir=None):
    """Which of `labels` have a launchd plist whose command reaches a BROWSER suite. -> [label]

    Split out of the check so it can be driven by a fixture. A guard whose only input is his real
    machine can never be seen RED on purpose, and one that has not been seen red is measuring
    nothing. [[regression-guard]]

    Bounded: 200 KB per file. An unbounded sweep of this shape once pinned a core for 28 hours.
    """
    agents_dir = agents_dir or os.path.join(os.path.expanduser("~"), "Library", "LaunchAgents")
    guilty = []
    for lbl in labels:
        p = os.path.join(agents_dir, lbl + ".plist")
        if not os.path.isfile(p):
            continue
        # ⚠ `open`, not `io.open`: this module never imports io, so io.open raised NameError —
        # which the bare `except Exception: continue` below swallowed, making the scan return []
        # for EVERY job. The check would have shipped answering "no browser suite here" forever,
        # whatever was actually scheduled: a guard that can only say OK. Caught only because the
        # fixture demanded it be seen RED. And the except is narrowed for the same reason — an
        # OSError is a plist we cannot read; a NameError is a bug wearing its clothes.
        try:
            with open(p, encoding="utf-8", errors="replace") as fh:
                plist = fh.read(200000)
        except OSError:
            continue
        blob = plist
        for tok in plist.replace("<string>", " ").replace("</string>", " ").split():
            if tok.startswith("/") and os.path.isfile(tok):
                try:
                    with open(tok, encoding="utf-8", errors="replace") as fh:
                        blob += fh.read(200000)
                except OSError:
                    pass
        # ⚠ AN INVOCATION, NOT A MENTION. The first cut matched the bare substring "npx
        # playwright" and immediately accused routine_Q — a WATCHDOG whose only crime is the
        # alert string `run \`npx playwright install\``. It monitors the suites; it does not run
        # one. A guard that reads prose about the thing as the thing is the same defect that has
        # blinded three source guards in this repo already. [[feedback-comments-vs-code]]
        if _RUNS_A_BROWSER_SUITE.search(blob):
            guilty.append(lbl)
    return guilty


def _check_no_browser_suite_is_scheduled_on_this_mac():
    """Is any scheduled job running a BROWSER suite on his laptop? They belong on GitHub.

    Konyo's standing order, given six times: the browser suites run in CI, never on his Mac.
    On 2026-08-31 that order had been quietly broken for an unknown length of time and NOTHING
    could see it. Five launchd jobs — routine_H, I, J, K and L — each fired locally at the same
    minute as its own GitHub twin (`routine-i-playwright.yml` is `cron: '0 6 * * *'`, which is
    09:00 IDT, exactly what `ai.konyo.d2r.routine_I.plist` was set to). Someone had already made
    `.disabled` COPIES of all five, intending to switch them off, and never unloaded the live
    ones. Both copies sat side by side in ~/Library/LaunchAgents for months.

    WHAT IT COST, measured the morning it was found: eight chrome-headless-shell processes, three
    of them at 132%, 99% and 96% CPU at once on a 10-core machine, load average 8.75. He reported
    it as "my pc is hot and kinda laggy". It also blocked every push that morning — the pre-push
    hook bounds test_control at 600s, and a saturated machine cannot finish it in 600s, so two
    ships died with "⏱ test_control HUNG" and the cause looked like a test problem.

    A duplicated job is invisible in the worst way: BOTH copies work. CI is green, the local run
    is green, and the only symptom is heat. So the guard cannot ask "does it pass" — it has to
    ask WHERE IT RUNS. [[test-venue]] [[feedback-generalize-fixes]]

    ⚠ Bounded on purpose: at most 60 jobs, and only the first 200 KB of any script is read. An
    unbounded sweep of this shape once held a core at 99% for 28 hours on this same machine.
    """
    import subprocess as _sp
    if sys.platform != "darwin":
        return UNKNOWN, "this check only knows launchd, so it cannot speak for this machine"
    try:
        out = _sp.run(["launchctl", "list"], capture_output=True, text=True, timeout=10)
    except Exception as e:
        return UNKNOWN, "launchctl could not be asked: %s" % str(e)[:70]
    if out.returncode != 0:
        return UNKNOWN, "launchctl refused to list the jobs, so the venue is unknown"
    labels = []
    for ln in out.stdout.split("\n")[1:]:
        parts = ln.split("\t")
        if len(parts) >= 3 and parts[2].startswith(("ai.konyo", "com.konyo")):
            labels.append(parts[2].strip())
    labels = sorted(set(labels))[:60]
    if not labels:
        return OK, "no konyo job is scheduled on this machine at all"
    guilty = browser_suites_among(labels)
    if guilty:
        return MISSING, ("%d scheduled job(s) run a BROWSER suite on this Mac instead of on "
                         "GitHub: %s. They have CI twins; a local copy only adds heat and "
                         "starves the push gate (REG-416)" % (len(guilty), ", ".join(guilty)))
    return OK, ("no scheduled job runs a browser suite here \u2014 all %d are python or "
                "non-browser, and the suites stay on GitHub" % len(labels))

def _check_the_engines_CORROBORATE_each_other():
    """Do the engines agree with EACH OTHER, not merely with themselves?

    ⚠ v2228 — THE GAP THE OTHER TWENTY CHECKS CANNOT SEE. Every check above asks whether ONE engine
    is well. Every serious defect found on 2026-08-28 was a pair of numbers that were each correct
    and wrong TOGETHER, and not one of them could have been caught by asking either side alone:

        19 vs 2      the vault watchdog against reel_retention — seventeen unnecessary paid sweeps,
                     three of them over test fixtures
        1263 vs 403  the shadow ledger against the item universe — arithmetically impossible, and it
                     had already crossed the threshold that says "the record is worth a decision"
        157 vs 7     two payload fields both named `owned`
        36 vs 30     the sweep memory against the disk — nearly six read-records deleted as ghosts

    His words: "the system needs an eagle eye corroborator, the engines all communicating."

    tv/corroborate.py holds the invariants and NEVER writes, never averages, and never picks a side.
    UNKNOWN on either side is UNKNOWN here, never agreement.
    """
    try:
        sys.path.insert(0, HERE)
        import corroborate as _co
        st, say = _co.verdict()
    except Exception as e:
        return UNKNOWN, "the corroborator could not run: %s" % str(e)[:90]
    if st == _co.DISAGREE:
        return MISSING, say
    if st == _co.UNKNOWN:
        return UNKNOWN, say
    return OK, say


# ══ v2277 — THE HEALTH ENGINE, FOLDED INTO THE ONE EAGLE EYE ═══════════════════════════════════
#
# Konyo asked for "a system that does red/green flag us... one unit system engine locked in".
# The first cut of that was a SEPARATE module with its own CLI and its own four-state vocabulary —
# which would have been the FIFTH thing on this machine implementing "report, never repair, and
# never call an unmeasured thing fine". That is [[copy-drift]] exactly: one method in five places,
# four of which he would have to know to run.
#
# So `health_engine` keeps the CHECKS (it is unit-testable in isolation and every law in it is
# sabotage-proven) and this file keeps the SURFACE. Same pattern as "the other doctors": the eagle
# eye CALLS rather than re-implements. One rail, one payload, one place he looks.
#
# ⚠ THE STATE MAP LOSES A DISTINCTION AND THAT IS DELIBERATE. health_engine separates WARN from
# BLOCKED; this rail has only OK / MISSING / UNKNOWN, and adding a fourth state here would ripple
# through the healer's recheck map, the icon table and every consumer of /api/eagle. The severity
# survives in the DETAIL string, which is the part he actually reads. What must NOT be lost is
# UNKNOWN, and it is not: it maps to itself.
#: ⚠ ONE REPORT PER TICK, NOT FOUR. Each adapter would otherwise re-run the whole engine, and
#: `armed_migration` reads the 6MB bible.html — so four flags cost four full-file reads on a rail
#: that runs on a ten-minute timer at every console boot. The v2080 scar was exactly this shape:
#: two correct fixes that together put 17 seconds into the boot path. Short TTL, so a human
#: pressing the button twice still gets a fresh answer. [[two-fixes-broke-each-other]]
_health_cache = {"active": False, "rep": None}


def _health_report():
    import health_engine as HE
    if _health_cache["active"] and _health_cache["rep"] is not None:
        return _health_cache["rep"]
    # v2277 — HAND IT THE REAL BOARD READ. Without this the board_join flag is UNKNOWN for ever,
    # and a flag that can only ever say one thing is furniture, not a check.
    rep = HE.report(board=_board_read())
    if _health_cache["active"]:
        _health_cache["rep"] = rep
    return rep


def _clip(x, n):
    t = str(x)
    return t if len(t) <= n else t[:n - 1] + "\u2026"


def _health(check_id):
    """One health_engine check, in this rail's vocabulary. -> (state, detail)"""
    def run():
        try:
            import health_engine as HE
        except Exception as e:
            return UNKNOWN, "health_engine will not import: %s" % str(e)[:90]
        try:
            row = [r for r in _health_report()["rows"] if r["id"] == check_id]
        except Exception as e:
            return UNKNOWN, "the health engine raised: %s" % str(e)[:90]
        if not row:
            # a check that vanished must not read as a check that passed
            return UNKNOWN, "the health engine no longer reports '%s'" % check_id
        r = row[0]
        detail = r["line"]
        if r["evidence"]:
            # ⚠ ELLIPSIS, NOT A BARE CUT. The first cut printed "stamped-somewhere=T" — a
            # truncated True that reads as a value in its own right, which is exactly the shape
            # of a right number under a word that stopped being true. [[label-outlived-referent]]
            detail = "%s  [%s]" % (detail, "; ".join(_clip(x, 110) for x in r["evidence"][:2]))
        return ({HE.OK: OK, HE.WARN: MISSING, HE.BLOCKED: MISSING,
                 HE.UNKNOWN: UNKNOWN}.get(r["state"], UNKNOWN), detail)
    return run


#: ══ v2284 — WHOSE PROBLEM IS IT? ═══════════════════════════════════════════════════════════════
#:
#: Konyo, reading "4 need you": "4 need me? make sure to verify and fix what needs me for real".
#:
#: Measured the same minute — of the three the rail was counting against him, TWO were mine:
#:   extraction lanes  a code defect (#75): the vault lane cannot seal "examined, nothing here",
#:                     so it holds reels for ever. No amount of clicking fixes that.
#:   board join        a code defect (#76): _BOARD_WIN is assigned in a CHILD PROCESS the server
#:                     can never read. Also not his to fix.
#:   shadow gate       genuinely his — the Wilson rule and the live gate disagree on 38 of 401
#:                     names, and which rule to adopt is a judgement nobody else can make.
#:
#: A rail that bills him for my bugs teaches him the number is noise, and then the one line that
#: really is his gets skimmed with the rest. [[label-outlived-referent]]
#:
#: ⚠ THIS IS NOT A MUTE BUTTON. A check named here still renders, at its real state and colour —
#: it simply stops inflating the count of things HE can act on, and is listed under its own
#: heading with the task that owns it. Anything not named here counts as his, so a new check is
#: his by default and has to be argued out rather than in.
MINE = {
    "extraction lanes": "#75 — the vault lane cannot seal 'examined, nothing here'",
    "board join": "#76 — _BOARD_WIN is set in a child process the server cannot read",
}


def owner_of(name):
    """-> 'me' when a named code defect owns it, else 'you'."""
    return "me" if name in MINE else "you"


def _check_what_runs_without_him():
    """Nine loops run with no prompt from him, one of them a DELETION lane, and until v2293 nothing
    on this console could say what any of them would touch. The cold read asked "if this app were
    about to do something on your behalf, could you tell what it would do and what it would leave
    alone?" and answered CANNOT TELL. This reports the answer, and goes MISSING when a lane's own
    BODY contradicts the promise it publishes."""
    try:
        import auto_scope
    except Exception as e:
        return UNKNOWN, "auto_scope will not import, so nothing here knows what runs unprompted: %s" % str(e)[:80]
    try:
        import control_app
        broken = auto_scope.check_declarations(control_app)
        lanes = auto_scope.LANES
    except Exception as e:
        return UNKNOWN, "could not read the lane declarations: %s" % str(e)[:90]
    if not lanes:
        return UNKNOWN, "no lane declared a scope — a reader that finds nothing is broken, not clean"
    if broken:
        return MISSING, "%d lane(s) do what they promise never to do: %s" % (
            len(broken), "; ".join(broken)[:200])
    deleters = sorted(n for n, d in lanes.items() if "delete" not in (d.get("forbids") or []))
    return OK, "%d lanes run without you; %d can delete (%s), and no lane's own body contradicts " \
               "its promise" % (len(lanes), len(deleters), ", ".join(deleters) or "none")


def _check_every_ledger_can_say_WHERE_IT_CAME_FROM():
    """v2746 — ONE BOOLEAN IS ANSWERING A THREE-LEDGER QUESTION, AND ON THIS MACHINE IT IS NULL.

    Konyo, on Dean's fleet card: *"it should read he hasnt yet synced his uniques.. sets and
    runewords has been verified by him already and accepted"*. Three ledgers, three different
    sentences, and `control_ui.html:19562` renders one blanket band above all three from a single
    `t.onOwnerSeed`.

    ⚠⚠ THE DEFECT THIS ROW EXISTS FOR IS A DISAGREEMENT NO SINGLE COMPONENT CAN SEE, and it was
    live on his own console. OBSERVED 2026-09-06T18:49Z, on a tally 0.0 h old — not a stale read:

        /api/board_ownership        onOwnerSeed: true   (seedsBelongHere true, ledger KonyoEndgame)
        his own row on /api/fleet   tally.onOwnerSeed: null

    Sixteen minutes later the same two reads both said `true`, so the field FLICKERS rather than
    being permanently absent — which is worse to diagnose and is why this belongs in a doctor.

    THE MECHANISM, proven structurally rather than by timing: there are TWO tally producers and
    only one carries the field. `grail_tally()` reads the live board and publishes it
    (control_app.py:2010); when the app window is not showing the board it falls back to
    `_tally_from_board_store()`, whose returned keys are exactly

        ['at', 'ok', 'profile', 'runewords', 'sets', 'source', 'uniques', 'why']

    — measured on his tree, no provenance among them — because the record it reads is banked by
    `/api/board_tally` from six keys (`who, route, sets, uniques, runewords, at`,
    control_app.py:26538) and the board never posts the rest. So whichever producer answers decides
    whether the warning can appear at all, and UNKNOWN renders as no warning.
    [[the-unjoined-end]] [[copy-drift]]

    ⚠ AND UNKNOWN IS NOT CLEAN. A console that cannot say where its rows came from is exactly as
    unable to warn as one that is wrong about it — the difference is only that nobody can tell.
    [[unknown-stays-unknown]]

    FREE: one shared board read (the same one three other checks already fold into) plus the
    fleet payload this console already holds. No second poke at the window he is looking at.
    [[borrowed-surface]]
    """
    try:
        import ledger_authority as LA
    except Exception as e:
        return UNKNOWN, "ledger_authority will not import, so nothing can say where a row came " \
                        "from: %s" % str(e)[:80]

    tbl = LA.seed_table()
    if not tbl.get("ok"):
        # a parser that cannot find its subject must never read as "there are no seeds"
        return MISSING, ("the seed literals could not be read out of bible.html, so no ledger can "
                         "be told inherited from earned: %s" % str(tbl.get("why"))[:180])
    seeds = "; ".join("%s %d" % (k, v["n"]) for k, v in sorted(tbl["seeds"].items()))

    got = _board_read()
    fleet = _get("/api/fleet")
    if not got and not fleet:
        return UNKNOWN, "neither the board nor the fleet answered — nobody looked, so nothing is " \
                        "known about any ledger's provenance"

    board_seed = (got or {}).get("onOwnerSeed") if isinstance(got, dict) else None
    board_loaded = (got or {}).get("boardLoaded") if isinstance(got, dict) else None

    me = (fleet or {}).get("me") if isinstance(fleet, dict) else None
    rows = list((fleet or {}).get("online") or []) + list((fleet or {}).get("offline") or [])
    mine = next((m for m in rows if isinstance(m, dict) and m.get("machine") == me), None)
    wire_seed = ((mine or {}).get("tally") or {}).get("onOwnerSeed") if mine else None

    # ── THE CONTRADICTION, which is the finding rather than an error bar ─────────────────────
    if isinstance(got, dict) and got.get("ok") and board_loaded and board_seed is not None \
            and mine is not None and wire_seed != board_seed:
        return MISSING, (
            "this console's BOARD says onOwnerSeed=%r and its own FLEET ROW publishes %r — the "
            "card he reads is fed by the row, so right now the warning cannot appear here whatever "
            "the board says. Two tally producers, one field: grail_tally() carries it "
            "(control_app.py:2010) and _tally_from_board_store() cannot, because /api/board_tally "
            "banks only who/route/sets/uniques/runewords/at (control_app.py:26538), so the flag "
            "flickers with whichever producer answered. Fix: publish the provenance on the board's "
            "POST too, and per ledger. Seeds parsed: %s"
            % (board_seed, wire_seed, seeds))

    # ── the per-ledger sentence, derived from counts only; no name crosses the boundary ──────
    flagged, unknown_rows, deficits = [], [], []
    for m in rows:
        t = (m or {}).get("tally")
        if not isinstance(t, dict) or not t.get("ok"):
            continue
        who = (m.get("nickname") or m.get("machine") or "?")
        v = LA.classify_row(t, table=tbl)
        if t.get("onOwnerSeed") is None:
            unknown_rows.append(who)
            continue
        for led in v.get("ledgers") or []:
            if led.get("beyondSeed") is not None and led["beyondSeed"] < 0:
                deficits.append("%s %s %d/%s vs a seed of %s"
                                % (who, led["ledger"], led["have"], led["total"], led["seedN"]))
            elif led.get("provenance") == LA.SEEDED:
                flagged.append("%s %s %s of %s inherited"
                               % (who, led["ledger"], led["seedN"], led["have"]))

    if deficits:
        return MISSING, ("a board reports FEWER rows than the owner's seed would have written into "
                         "it, so its own progress cannot be separated from the seed by counting: "
                         "%s. That is a real gap in that store, not a rounding artefact — the "
                         "figure is negative and is reported as such rather than clamped to zero."
                         % "; ".join(deficits[:4]))
    if board_seed is None and not flagged and unknown_rows:
        return UNKNOWN, ("no console on the fleet could say whether its rows came from the owner's "
                         "seed (%s) — UNKNOWN, not clean. Seeds parsed: %s"
                         % (", ".join(sorted(set(unknown_rows))[:4]), seeds))
    return OK, ("every ledger can state its provenance; %d parsed seed(s) [%s]%s"
                % (len(tbl["seeds"]), seeds,
                   ("; flagged: " + "; ".join(flagged[:4])) if flagged else "; none inherited"))


def _check_no_ledger_FIGURE_has_gone_stale_unnoticed():
    """v2746 — THE SEED SAT 46 FINDS BEHIND FOR MONTHS AND NOTHING WAS WATCHING AGE AT ALL.

    Konyo: *"_GRAIL_SEED 245 uniques but this is my owner seed.. and even that is so outdated.. its
    at 292/403 we already said and sets 123/135.... it needs to auto update and not be stale"* and
    then *"connect it all to the heart of the console so nothing becomes stale again"*.

    ⚠⚠ THIS IS DELIBERATELY NOT A SEED CHECK. A seed-specific row would fix one frozen constant and
    leave the next one to rot identically. It walks EVERY ledger figure by KIND — live reads, other
    machines' beacons, hardcoded constants — so a constant added tomorrow is graded the day it
    appears.

    ⚠⚠ AND THE FROZEN ONES ARE GRADED BY **DRIFT**, NEVER BY AGE. This is the single way the whole
    fix could have gone quietly vacuous: re-parsing bible.html every tick makes the READ fresh and
    leaves the VALUE exactly as old, so a watchdog that timed the read would report every seed as
    seconds old forever while it drifted by fifty finds. Nothing anywhere records when a seed was
    transcribed, so its age is not merely unknown — it is unmeasurable, and `ageKnown` is False for
    that KIND regardless of any timestamp. What IS measurable is how far it has fallen behind the
    live figure. MEASURED on his board: uniques seed 246 against a live 292 (46 behind), sets seed
    108 against 123 (15 behind), runewords 99 against 99 (level).
    [[stale-reading]] [[unknown-stays-unknown]]

    ⚠ THE BEACON THRESHOLD IS DERIVED FROM THE PIPELINE IT GRADES, not invented: the beacon fires
    every 240 s, `_TALLY_TTL_S` caches the tally, `fleet_presence` caches the roster 60 s, so a
    perfectly healthy figure is legitimately that sum old. The stale line is a multiple of the whole
    chain and the row shows its arithmetic — a threshold under the floor cries wolf and one over the
    ceiling never fires, and both look exactly like no threshold at all.
    [[feedback-threshold-above-the-ceiling]]

    FREE: reuses the one shared board read and the fleet payload the console already holds.
    """
    try:
        import ledger_authority as LA
    except Exception as e:
        return UNKNOWN, "ledger_authority will not import, so no figure's age is known: %s" % str(e)[:80]

    got = _board_read()
    fleet = _get("/api/fleet")
    if not got and not fleet:
        return UNKNOWN, ("neither the board nor the fleet answered — no figure could be dated, "
                         "which is UNKNOWN and not the same as everything being fresh")
    try:
        st = LA.staleness(own=got if isinstance(got, dict) else None,
                          fleet=fleet if isinstance(fleet, dict) else None)
    except Exception as e:
        return UNKNOWN, "the staleness walk raised: %s" % str(e)[:110]

    rows = st.get("rows") or []
    if not rows:
        # a reader that finds nothing to grade is broken, not clean
        return UNKNOWN, "no ledger figure could be enumerated at all — a watchdog with nothing in " \
                        "front of it is not a pass"
    ceil = st["ceiling"]
    drifted = [r for r in rows if r.get("kind") == LA.FROZEN and r.get("stale") is True]
    old = [r for r in rows if r.get("kind") == LA.BEACON and r.get("stale") is True]
    dark = [r for r in rows if r.get("stale") is None]

    if drifted or old:
        bits = []
        for r in drifted:
            # NAME the figure and say HOW FAR, never a count — a count alone is not actionable
            bits.append("%s is %+d behind the live figure (value %s, newest date it records %s, "
                        "AGE UNKNOWN — a hardcoded literal records no transcription time)"
                        % (r["name"], r["drift"], r["value"], r.get("newestFindDate") or "none"))
        for r in old:
            bits.append("%s last spoke %.1f min ago (stale past %.1f min)"
                        % (r["name"], (r["ageMs"] or 0) / 60000.0, ceil["staleMs"] / 60000.0))
        return MISSING, ("%d of %d ledger figure(s) are out of date: %s. Threshold arithmetic: "
                         "beacon %.0fs + tally TTL %.0fs + fleet cache %.0fs = %.0fs ceiling, "
                         "x%d = %.0fs stale line (%s)."
                         % (len(drifted) + len(old), len(rows), "; ".join(bits[:4]),
                            ceil["parts"]["beaconPeriodS"], ceil["parts"]["tallyTtlS"],
                            ceil["parts"]["fleetCacheS"], ceil["ceilingMs"] / 1000.0,
                            ceil["parts"]["multiple"], ceil["staleMs"] / 1000.0, ceil["how"]))
    if dark:
        return UNKNOWN, ("%d of %d ledger figure(s) could not be dated at all (%s) — UNKNOWN age is "
                         "not a fresh one" % (len(dark), len(rows),
                                              ", ".join(r["name"] for r in dark[:4])))
    return OK, ("%d ledger figure(s) are current; every frozen constant is level with its live "
                "figure and every beacon is inside %.0f min"
                % (len(rows), ceil["staleMs"] / 60000.0))


def _check_read_names_lane(*_a, **_k):
    """Where the already-read names would go: the auto door, or his hand.

    ⛔ THIS ROW GOES RED ONLY ON MACHINE WORK. Names waiting on HIM are not a fault — his ruling of
    2026-09-07 makes the manual lane the correct destination for a rare (*"manual is the path for
    rares"*), so counting them as red would make the row cry wolf about the design working. Same
    discipline as `_BY_DESIGN_STATIONS` on the river row: an exemption with a stated reason, so it
    can be audited instead of silently growing.

    ⚠ WHAT WOULD MAKE IT RED: a name that CLEARS the witness bar, IS on a roster, has ONE
    referent, and still is not banked — the auto lane owing work it can do for free.

    ⚠ v3008 — HELD IS NOT OWED, AND THE DOOR NOW SAYS WHY. Measured live: ONE name clears the bar
    (Crescent Moon), and its name has multiple referents (two uniques share it, plus the
    Shael+Um+Tir runeword) — two witnesses corroborate a NAME, not an ITEM, so auto-banking would
    pick one of three referents on evidence that cannot distinguish them. The refusal was always
    correct; before this, the row reported it as owed work ("can take those for free"), which is
    a correct hold wearing a fault's clothes. (The earlier docstring's "today that count is 0"
    was measured true when written and is not now — judge the measurement, not the prose.)
    """
    try:
        import read_names_lane as _RNL
    except Exception as exc:
        return UNKNOWN, ("read_names_lane could not be imported (%s), so where the read names "
                         "would go is UNKNOWN" % type(exc).__name__)
    try:
        sp = _RNL.split()
    except Exception as exc:
        return UNKNOWN, "the read-names lane raised (%s) - UNKNOWN, not clean" % type(exc).__name__
    if not isinstance(sp, dict) or not sp.get("ok"):
        return UNKNOWN, ("the read-names lane could not measure: %s"
                         % str((sp or {}).get("why") or "no reason given")[:130])
    # ⚠ None is not 0. An unreadable roster means the classification never happened.
    if sp.get("tickable") is None:
        return UNKNOWN, ("the rosters could not be read (%s), so which read names could ever tick "
                         "is UNKNOWN" % str(sp.get("rosterWhy") or "")[:90])
    auto_t = sp.get("autoTickable") or 0
    tick = sp.get("tickable") or 0
    furn = sp.get("furniture") or 0
    _owed = sp.get("autoOwed")
    _held = sp.get("autoHeld")
    if _owed is None or _held is None:
        # an older lane (or an unreadable roster) cannot say held-vs-owed — fall back to the
        # blunt count rather than inventing the distinction
        if auto_t:
            return MISSING, ("%d read name(s) clear %d witness(es), are on a roster, and are "
                             "still not banked - and this lane predates the held/owed split, so "
                             "WHY cannot be told from here" % (auto_t, sp.get("minWitnesses")))
    else:
        if _owed:
            return MISSING, ("%d read name(s) clear %d witness(es), are on a roster with ONE "
                             "referent each, and are still not banked - the auto door can take "
                             "%s for free, the reading is already paid for"
                             % (len(_owed), sp.get("minWitnesses"), ", ".join(_owed[:6])))
        if _held:
            _v = "; ".join("%s (%d referents: %s)"
                           % (h.get("name"), len(h.get("referents") or []),
                              "/".join(h.get("referents") or []))
                           for h in _held[:4])
            return OK, ("the auto door is HOLDING %d name(s), and says why: %s. Two witnesses "
                        "corroborate a NAME, not an ITEM - banking would pick one referent on "
                        "evidence that cannot distinguish them. Correct hold, not owed work; his "
                        "hand stays the only door for these." % (len(_held), _v))
    return OK, ("no read name is owed to the auto lane. %d of %d read name(s) could ever tick and "
                "all of them fall to HIS hand (single-sighting, which is the normal case for a "
                "rare); %d more are locked-inventory fixtures that can never tick and account for "
                "over half of every sighting."
                % (tick, sp.get("names"), furn))


def _check_the_stage_shows_what_the_dom_claims(*_a, **_k):
    """Does the SCREEN agree with the DOCUMENT about the room? The contradiction is the finding.

    His words, 2026-09-07, over a photograph of a black room with the shelf open: *"connect it to
    the heart of the console too"*.

    MEASURED at that moment: shelf {open, filled, cards 3090} and theatre {open, loaded, painted,
    ink} — 3,090 cards built and the console calling itself painted, while he looked at black.

    ⚠⚠ THE SHELF DOOR HAS BEEN HARDENED THREE TIMES FOR THIS SAME COMPLAINT (v2446 swallowed,
    v2451 toggles, v2666 prove-from-the-rect), and every one of those guards proves the DOCUMENT.
    `painted` and `ink` are DOM measurements wearing pixel names. This row is the first thing in
    the console that holds the DOM's claim and the screen's reading side by side.

    ⚠ RED ONLY ON DISAGREEMENT. A dark room with nothing open is correct; an unlookable or covered
    window is UNKNOWN. Neither is a fault, and grading either as one would make this row cry wolf
    on the homepage. [[feedback-contradiction-is-the-finding]] [[unknown-stays-unknown]]
    """
    try:
        import stage_witness as _SW
    except Exception as exc:
        return UNKNOWN, ("stage_witness could not be imported (%s), so whether the screen agrees "
                         "with the DOM is UNKNOWN" % type(exc).__name__)
    try:
        v = _SW.verdict()
    except Exception as exc:
        return UNKNOWN, "the stage witness raised (%s) - UNKNOWN, not clean" % type(exc).__name__
    st = str((v or {}).get("state") or "UNKNOWN")
    why = str((v or {}).get("why") or "no reason given")[:300]
    if st == "CONTRADICTION":
        return MISSING, why
    if st == "AGREE":
        return OK, why
    return UNKNOWN, why


def _check_the_river_walk_is_walking(*_a, **_k):
    """Is anything actually WATCHING the river, and when did it last look?

    Konyo, 2026-09-07: *"honest and accurate and pinpointed of course.. i want it visually synced
    to the backend"* — of the shelf-as-river view he asked for.

    ⚠⚠ THE SILENCE THIS BREAKS. `_retro_triage_loop` walks the river every tick and reports two of
    three outcomes: it prints transitions when something MOVED and "NOT WALKED" when the walk
    FAILED. A successful walk finding NOTHING printed nothing and stored nothing. MEASURED before
    this row existed: 40 stamps, all `by: claude:first-wiring`, newest 12.8h old, 0 carrying a
    `from` — not one row written by the loop. That is equally consistent with "the river is still"
    and "the loop never runs", and nothing could tell them apart.

    ⛔ IT DOES NOT GO RED ON A STILL RIVER. `moved: 0` is a perfectly good answer — most ticks find
    nothing, by design, and a row that reddens on the normal case is a row he stops reading. It
    goes red on the WATCHING stopping, not on the water being calm.
    [[feedback-silence-is-not-evidence]] [[unknown-stays-unknown]]
    """
    # ⚠⚠ v3012 — THIS ROW MEASURED A DEAD TWIN FOR ITS ENTIRE LIFE. It did `import control_app`
    # and read `river_walk_state()` — a MODULE GLOBAL. The console runs control_app as its own
    # process entry, so that import builds a SECOND module instance whose _RIVER_WALK is the empty
    # literal: at=None, in every process, since the row was born. PROVEN by one payload read two
    # ways at the same instant: /api/status.riverWalk said walks=13, at 15s old, while this row's
    # eagle copy said "has not completed a tick in this process — unaskable for 4d (1468
    # attempts)". Four days of UNKNOWN about a walk that ran the whole time. The WIRE is the one
    # authority — the serving process publishes its own _RIVER_WALK there — and it is honest from
    # a standalone doctor process too, which the import never was.
    # [[the-unjoined-end]] [[feedback-suspect-the-instrument]]
    _stw = _get("/api/status") or {}
    st = _stw.get("riverWalk")
    if st is None:
        return UNKNOWN, ("the console did not answer (or predates the riverWalk field), so "
                         "whether the river is being walked is UNKNOWN")
    if not isinstance(st, dict):
        return UNKNOWN, "the river walk state is unreadable"
    if st.get("at") is None:
        # ⚠ NEVER "no movement". Nobody has looked yet in that process.
        return UNKNOWN, str(st.get("why") or "the river walk has never completed a tick there")
    import time as _t
    age = round(max(0.0, _t.time() - float(st["at"])), 1)
    if st.get("ok") is False:
        return MISSING, ("the last river walk FAILED %ss ago: %s"
                         % (age, str(st.get("why"))[:150]))
    # a walk older than several ticks means the loop has stopped, not that the water is calm
    if isinstance(age, (int, float)) and age > 900:
        return MISSING, ("nothing has walked the river for %.0f minute(s) — the loop reports every "
                         "tick, so this is the WATCHER stopping rather than a still river"
                         % (age / 60.0))
    return OK, ("walked %ss ago: %s reel(s) compared, %s moved (%s walk(s) this process). A still "
                "river is the normal answer; this row goes red when the WATCHING stops."
                % (age, st.get("reels"), st.get("moved"), st.get("walks")))


#: ══ v#### — THE FOUR ROUTES GET FOUR ROWS, SO ONE CAN GO RED ALONE ════════════════════════════
#:
#: ⚠⚠ MEASURED 2026-09-08 over the fifty rows below: the ones that touch a reel's route are
#: `extraction lanes`, `vault stores`, `vault proposal`, `read names lane` and `names banked`, and
#: NOT ONE of them is per-route. `extraction lanes` watches lane_health's two SWEEP lanes
#: (chronicle, vault) — a different axis entirely — and inventory and stash shared its single
#: "vault" bucket. chronicle-sets and chronicle-uniques were indistinguishable to every supervisor
#: in this file. If exactly one of the four routes died, every row here stayed green. A rail that
#: cannot name WHICH of four things broke is not watching four things.
#:
#: ⚠ AND THESE FOUR SHOW UNKNOWN ON HIS OWN MACHINE, WHICH IS THE POINT AND NOT A GAP. Measured
#: over his 49 reels: stash 11, inventory 2, chronicle 1 — and that one chronicle reel recorded no
#: ledger, so both chronicle routes are taken by ZERO reels. A row that could only ever read his
#: live store would be green forever and prove nothing; it reads UNKNOWN, and the gate
#: (test_the_four_routes_go_red_alone) supplies the input his footage never has.
#: [[gate-blind-to-unexercised-input]] [[unknown-stays-unknown]]
_routes_cache = {"active": False, "got": None}


def _route_census_once():
    """The four-route census, live. -> dict. An owner that will not answer is UNKNOWN, never OK."""
    try:
        import reel_templates as _RT
        return _RT.route_census()
    except Exception as e:
        return {"ok": False, "state": "UNKNOWN", "order": [], "routes": {},
                "why": "reel_templates would not answer (%s), so nothing is known about any "
                       "route" % str(e)[:90]}


def _route_read():
    """ONE census per tick. Four checks ask the same question and the answer walks the river.

    ⚠ SCOPED TO `run()` EXACTLY LIKE `_board_read`, and for the reason written there: a
    module-level cache with a TTL swallows a test's stub and serves the previous test's answer.
    A check called on its own always reads fresh, which is what every caller outside the rail
    expects. [[feedback-suspect-the-instrument]]
    """
    if _routes_cache["active"]:
        return _routes_cache["got"]
    return _route_census_once()


def _route_health(route):
    """One of the four reel routes, ALONE. -> (name-bound fn) -> (state, detail)"""
    def run():
        cen = _route_read()
        rows = (cen or {}).get("routes") if isinstance(cen, dict) else None
        if not isinstance(rows, dict) or not rows:
            return UNKNOWN, ("the four-route census could not be read, so nothing is known about "
                             "the %s route: %s" % (route, str((cen or {}).get("why"))[:110]))
        r = rows.get(route)
        if not isinstance(r, dict):
            # a route that VANISHED from the census must never read as a route that passed
            return UNKNOWN, ("reel_templates no longer reports a %r route — it declares %s. A "
                             "route that disappeared is not a route that is well"
                             % (route, ", ".join(sorted(rows)) or "none"))
        st = str(r.get("state") or "")
        return ({"OK": OK, "BROKEN": MISSING}.get(st, UNKNOWN),
                str(r.get("why") or "the census gave no reason, so this route is UNKNOWN"))
    return run


def _check_the_fleet_lane_is_reachable():
    """★ THE FLEET WENT UNREACHABLE ON HIS SCREEN AND NOTHING IN THE HEART KNEW THE WORD.

    2026-09-09 11:07, photographed from his own console: the FLEET card read
    `fleet unreachable — <urlopen error _ssl.c:1112: The handshake operation timed out>` while the
    heart's own footer two inches below said `♥ 8 dark` — and not one of those 8 was the fleet.
    Measured at the time: `grep -c fleet` was **0** in heart.py AND in lane_census.py, and CHECKS
    carried no fleet row. The lane was not failing its supervision; it HAD none. That is the
    registered-vs-existing gap (21 threads, 11 registered) with a name on it, and it is the first
    of the unregistered ten to fail somewhere he could see. [[the-unjoined-end]]

    ⚠⚠ IT READS THE CACHE AND NEVER FETCHES. fleet_presence() spends up to 6 SECONDS against an
    unreachable site, and that is the exact condition this row exists to notice — so a check that
    called it would add its own six-second stall to every doctor pass at precisely the moment the
    console is already degraded. Same rule _heart2_census() follows: read what the producer last
    wrote; never re-run the producer inside a request. [[poll-slower-than-its-interval]]

    ⚠⚠ IT IS DERIVED FROM THE SAME STATE THE CARD PAINTS, ON PURPOSE. His complaint was not that
    the fleet was down — it was that the SCREEN and the HEART disagreed while sitting two inches
    apart. A row computed from a second source could reproduce that disagreement in a new place, so
    this one reads `_FLEET_PRESENCE_CACHE`, which is what `/api/fleet` serves the panel from.

    ⚠ FOUR OUTCOMES, NOT TWO. "Never asked" is not "reachable"; and "unreachable holding a roster"
    is not "unreachable holding nothing" — the first still has something honest to put on the card,
    the second leaves him with a blank and is the only unrecoverable one. Collapsing them would
    grade a cold console as a broken one and hide the case that actually cannot be rendered.
    [[unknown-stays-unknown]] [[zero-needs-a-denominator]]
    """
    import time as _t
    try:
        import control_app as _ca
    except Exception as e:
        return UNKNOWN, "control_app will not import (%s), so the fleet lane is unmeasured" % str(e)[:60]
    try:
        cache = _ca._FLEET_PRESENCE_CACHE
    except Exception as e:
        return UNKNOWN, ("control_app no longer exposes _FLEET_PRESENCE_CACHE (%s) — a cache that "
                         "vanished is not a fleet that is well" % type(e).__name__)
    last = cache.get("d")
    good, good_t = cache.get("goodD"), float(cache.get("goodT") or 0.0)
    now = _t.time()

    if last is None:
        # ⚠ NOT OK. A console that has never asked knows nothing about the fleet, and saying "ok"
        # here would mean the row reads green for the entire window in which it is most blind.
        return UNMEASURED, ("this console has not asked the site for the roster yet, so whether the "
                            "fleet is reachable is UNKNOWN — it is not 'reachable'")

    if last.get("ok") is not False:
        on = len(last.get("online") or [])
        off = len(last.get("offline") or [])
        age = round(max(0.0, now - float(cache.get("t") or 0.0)), 1)
        return OK, ("the site answered %ss ago — %d online, %d offline, %d machine(s) known"
                    % (age, on, off, on + off))

    why = str(last.get("error") or "no reason given")[:90]
    if good is None:
        return MISSING, ("the fleet is UNREACHABLE and this console has never received a roster, so "
                         "the panel has nothing honest to show at all — not a stale list, not a "
                         "count. Reason: %s" % why)
    g_on = len(good.get("online") or [])
    g_off = len(good.get("offline") or [])
    dur = round(max(0.0, now - good_t), 1) if good_t else None
    return MISSING, ("the fleet is UNREACHABLE%s, but a roster from that last contact is still in "
                     "hand — %d online, %d offline, %d machine(s) — so the panel can degrade to a "
                     "STALE list instead of a blank. Reason: %s"
                     % (("" if dur is None else " and has been for %ss" % dur),
                        g_on, g_off, g_on + g_off, why))


def _check_the_shelf_lanes_are_still_reading():
    """★ A LANE THAT STOPS READING MUST GO RED ON ITS OWN — Konyo, 2026-09-10, which is what
    `shelf_driver.py` was written for at v2909 (REG-908). It shipped 773 lines, a registered gate
    and 11 declared red-proofs, and then nothing ran it unattended.

    MEASURED 2026-09-11: `control_app.py` imports the module under TWO aliases (`_sd`, `_sd_lane`)
    and calls NOTHING on either — it reads only the constants `OWED_BY` and `READ_CLEARS`. An
    import with no call is the purest form of [[the-unjoined-end]]. His stored beat was **31.6
    hours old** and no supervisor anywhere said so: the lane was not failing its supervision, it
    HAD none — the same registered-vs-existing gap the fleet row above was added for.

    ⚠⚠ IT READS THE STORED BEAT AND NEVER RE-RUNS THE PRODUCER. `lane_census()` walks the lanes;
    calling it inside a doctor pass would add that walk to every request at exactly the moment the
    console is already degraded — the rule `_check_the_fleet_lane_is_reachable` states in its own
    docstring, and the one `_heart2_census()` follows. A stale beat IS the finding; re-running the
    producer would erase the very evidence this row exists to report. [[poll-slower-than-its-interval]]

    ⚠ AN ABSENT BEAT IS UNMEASURED, NOT HEALTHY. A driver that has never run says nothing about
    the lanes, and reporting that as OK is the zero-with-no-denominator this repo keeps paying for.
    [[unknown-stays-unknown]] [[zero-needs-a-denominator]]
    """
    try:
        import shelf_driver as _sd
    except Exception as e:
        return UNKNOWN, ("shelf_driver will not import (%s), so whether the lanes are still "
                         "reading is UNMEASURED" % str(e)[:60])
    try:
        beat = _sd.last_beat()
    except Exception as e:
        return UNKNOWN, ("the shelf driver could not be asked for its last beat (%s) — UNMEASURED, "
                         "not clean" % type(e).__name__)
    if not isinstance(beat, dict) or not beat.get("at"):
        return UNMEASURED, ("the shelf driver has never recorded a beat, so whether any lane is "
                            "still reading is UNKNOWN — it is not 'fine'")
    try:
        age_h = (time.time() * 1000.0 - float(beat["at"])) / 3600000.0
    except Exception:
        return UNKNOWN, "the stored beat carries an unreadable timestamp, so its age is UNKNOWN"
    owed = beat.get("owed")
    held = beat.get("held")
    tail = ("" if owed is None and held is None
            else " — it last reported %s owed, %s held, %s on disk"
                 % (owed, held, beat.get("onDisk")))
    if age_h >= _SHELF_BEAT_STALE_H:
        return MISSING, ("the shelf driver last beat %.1f HOURS ago (bar: %.0fh), so a lane that "
                         "stopped reading would not have been noticed%s"
                         % (age_h, _SHELF_BEAT_STALE_H, tail))
    if not beat.get("ok", True):
        return MISSING, ("the shelf driver's last beat %.1fh ago reported NOT ok: %s"
                         % (age_h, str(beat.get("why") or "no reason given")[:90]))
    # ⚠⚠ v2957 — `ok` IS ABOUT THE PLAN, NOT ABOUT A LANE, AND THIS ROW IS ABOUT LANES.
    # `beat["ok"]` is true whenever retention's plan was READABLE. A lane can be DARK or STALLED
    # underneath a perfectly readable plan, and until now this row would have said "reported ok"
    # over the top of it. That is REG-908's original complaint intact: `vaultAutoread` read 0 with
    # lastTs null for weeks and nothing said so. Wiring a producer WITHOUT this widen would have
    # flipped the row from permanently-MISSING to permanently-OK and left the fault unsurfaced —
    # a green that lies, bought with a fix. [[zero-needs-a-denominator]]
    # ⚠ AN ABSENT `laneCounts` KEEPS THE PRE-WIDENING ANSWER. His stored record predates the field,
    # and a legacy row must not be refused for lacking a key it COULD NOT HAVE HAD — the same
    # backward-compatibility rule REG-948 was written for. Absent is UNKNOWN about lanes, and
    # UNKNOWN here is reported as the old OK plus a note, never as a new failure.
    _lc = beat.get("laneCounts")
    if isinstance(_lc, dict) and _lc:
        _bad = {k: v for k, v in _lc.items()
                if str(k).upper() in ("DARK", "STALLED") and isinstance(v, int) and v > 0}
        if _bad:
            return MISSING, ("the shelf driver beat %.1fh ago, but %s — a lane in that state has "
                             "stopped reading and the plan being readable does not cover it%s"
                             % (age_h, ", ".join("%d %s" % (v, k) for k, v in sorted(_bad.items())),
                                tail))
        return OK, ("the shelf driver beat %.1fh ago and every lane it counted is reading (%s)%s"
                    % (age_h, ", ".join("%s %s" % (v, k) for k, v in sorted(_lc.items())), tail))
    return OK, ("the shelf driver beat %.1fh ago and reported ok; it recorded no per-lane counts, "
                "so whether each lane is reading is UNKNOWN rather than confirmed%s" % (age_h, tail))


#: How old a shelf beat may be before a lane that stopped reading would go unnoticed. His driver
#: is a per-session tool, not a timer, so this is deliberately generous — it exists to catch a
#: driver that has FALLEN SILENT FOR A DAY, not one that has not run in an hour.
_SHELF_BEAT_STALE_H = 12.0

def _check_the_running_code_is_the_code_on_disk():
    """★ IS THE CONSOLE EXECUTING WHAT THE FILE SAYS? — task #67, and the one question the drift
    lane cannot answer.

    `drift_state()` compares the RUNNING version stamp against the DISK version stamp. Both are
    LABELS. Two different images can carry the same stamp, and he EXECS THE WORKING TREE — so every
    save to control_app.py that does not bump a version is a change the drift lane is blind to and
    this one can see.

    ⚠ IT ASKS THE CONSOLE, IT DOES NOT HASH ITS OWN IMPORT. This doctor may run in a different
    process; hashing `control_app` from here would measure THIS process's import and report it as
    the console's. Only the console knows what the console loaded, so the sha comes over the wire
    from `/api/status`'s `proc` block. [[borrowed-surface]]
    ⚠ AN OLDER CONSOLE HAS NO `srcSha`, AND THAT IS UNMEASURED, NOT CLEAN. A console started before
    v2961 publishes no such key; reporting that as OK would be the zero-with-no-denominator this
    file keeps paying for. [[unknown-stays-unknown]]
    """
    d = _get("/api/status")
    if not isinstance(d, dict):
        return UNKNOWN, ("the console could not be asked what code it is running, so whether it "
                         "matches the disk is UNMEASURED")
    proc = d.get("proc")
    if not isinstance(proc, dict) or not proc.get("srcSha"):
        return UNMEASURED, ("this console publishes no source hash — it was started before the "
                            "check existed, so what it is running cannot be compared to the disk. "
                            "That is UNMEASURED, not a match")
    name = str(proc.get("src") or "control_app.py")
    disk = None
    try:
        import hashlib
        with open(os.path.join(HERE, name), "rb") as fh:
            disk = hashlib.sha1(fh.read()).hexdigest()
    except Exception as e:
        return UNKNOWN, ("%s could not be read from disk (%s), so the comparison is UNMEASURED"
                         % (name, type(e).__name__))
    running = str(proc.get("srcSha"))
    if running != disk:
        return MISSING, ("the console is running BYTES THAT ARE NO LONGER ON DISK: it loaded %s "
                         "(%s...) and the file now hashes %s... — every save to this file is a "
                         "deploy here, and this one has not been picked up. Relaunch to adopt it."
                         % (name, running[:10], disk[:10]))
    return OK, ("the console is running exactly what %s holds on disk (%s...)" % (name, disk[:10]))


def _check_the_shelf_is_where_it_says_it_is():
    """THE CORROBORATOR FOR HIS BLANK STAGE — a fill and a rect that can contradict each other.

    GROKBOT, 2026-09-12, with `ver` and `liveVer` BOTH v2988: the shelf stage is an EMPTY DARK
    PANEL — no cards, no headings — and two stage crops 5s apart are BYTE-IDENTICAL, so it is not
    a slow paint. At that same moment the console's own beat said `filled=true, cards~535,
    ink=true`, and a headless probe against the same server built 530 cards with no JS error.

    Both readings were honest. A DOM can be fully built inside a container that occupies no
    pixels, and the beat published a FILL and never a RECT — so nothing in it could contradict
    his eyes. v2996 puts the overlay's rect on the wire; this is the row that reads the two
    together, because either half alone says nothing. [[the-unjoined-end]]

    ⚠ CLOSED IS NOT A FAULT. The shelf is an on-demand overlay and is shut almost always. This
    row fires only when it is OPEN and not on screen.
    """
    st = _get("/api/status") or {}
    ub = st.get("uiBeat") if isinstance(st.get("uiBeat"), dict) else None
    if not ub:
        return UNKNOWN, "the console did not report a heartbeat, so nothing is known about the shelf"
    if not ub.get("n"):
        return UNKNOWN, "no console has ever checked in — headless, not healthy"
    # ⚠⚠ v3002 — THIS ROW ISSUED TWO BRAND-NEW `MISSING` VERDICTS OFF A BEAT OF UNKNOWN AGE, in
    # the same file whose sibling row hard-codes STALE_S for exactly this reason. `ub["n"]` only
    # says a console checked in ONCE, EVER. Close the console with the shelf open and a card below
    # the fold — or let WebKit suspend the beat's setInterval, the documented v2348 failure — and
    # three hours later this would still read that frozen panels dict and report THE SHELF OPENS ON
    # NOTHING about a window that is not on screen at all. [[stale-reading]]
    _bage = ub.get("ageS")
    if _bage is None:
        return UNKNOWN, ("the console reports no beat age, so how old this panels reading is "
                         "cannot be told — and a verdict on a reading of unknown age is a guess")
    if _bage > 300.0:
        return UNKNOWN, ("the console's last beat is %.0fs old, so its panels reading describes a "
                         "window nobody has heard from since. Nothing is known about the shelf NOW."
                         % _bage)
    panels = ub.get("panels")
    if not isinstance(panels, dict) or not panels:
        return UNKNOWN, "this console does not report its panels — unknown, not clear"
    shelf = panels.get("shelf")
    if shelf is None:
        return UNKNOWN, ("this console reports no shelf overlay at all (o.shelf is null) — it is "
                         "not in this build, which is not the same as it being fine")
    if not isinstance(shelf, dict):
        return UNKNOWN, ("the shelf field is %s, not the {open, filled, cards, why} object this "
                         "row reads — something changed its TYPE" % type(shelf).__name__)
    state = shelf.get("box")
    if state is None:
        return UNKNOWN, ("this console predates v2996 and publishes a shelf FILL with no RECT — "
                         "the exact gap that let a blank stage and cards~535 coexist. Restart it, "
                         "or where the overlay sits stays unmeasurable from here.")
    if state == "closed":
        return OK, "the shelf overlay is shut — a fact, not a fault"
    cards = shelf.get("cards")
    grid = shelf.get("gridCards")
    if state == "shown":
        # ⚠⚠ v2998 — "THE PAIR IS THE POINT" AND THE PAIR WAS ONLY EVER PRINTED. `box == "shown"`
        # returned OK whatever the fill said, so an overlay that is open, on screen and EMPTY —
        # which is the failure he photographed — read as healthy. The page already computes the
        # verdict in `why` ("the shelf overlay is open and carries no cards and no text") and this
        # file had ZERO readers of it. A corroborator whose second half never reaches the verdict
        # is one half wearing the name of two. [[the-unjoined-end]] [[plumbing-with-no-tap]]
        # ⚠⚠ v3001 — THE v2998 PREDICATE FIRED ON A CORRECT UI STATE AND COULD NOT FIRE ON THE
        # REAL ONE. `filled` is `!!(_cards > 0 || _txt > 40)` and the overlay always ships its own
        # heading and status chrome, so `filled` is ALWAYS true while open and `why` is ALWAYS
        # null — the first disjunct was unreachable, and the second (`cards == 0 and grid == 0`)
        # matches the DELIBERATE "No runs recorded yet" hero. So it reported MISSING about a
        # console behaving correctly, while printing "the page itself says: filled=false" over a
        # payload that said filled=true. A row that cries wolf is one he learns to skip.
        _vis = shelf.get("visibleCards")
        if shelf.get("emptyHero") is True:
            return OK, ("the shelf is open and on screen and has no runs to show yet — the empty "
                        "hero is rendered, which is the correct state, not a fault")
        _empty = (isinstance(_vis, int) and _vis == 0) or (cards == 0 and grid == 0)
        if _empty:
            return MISSING, ("THE SHELF IS OPEN AND ON SCREEN AND SHOWS NO REEL — %sx%s at top %s; "
                             "%s card(s) built, %s visible. The box is real and the empty-hero is "
                             "NOT rendered, so this is neither a layout fault nor an honest empty "
                             "shelf: something was built and none of it is on screen."
                             % (shelf.get("w"), shelf.get("h"), shelf.get("top"),
                                "UNKNOWN" if grid is None else grid,
                                "UNKNOWN" if _vis is None else _vis))
        # ⚠⚠ v2999 — A REAL BOX WITH EVERY CARD BELOW ITS OWN FOLD IS THE FAULT HE PHOTOGRAPHED.
        # v2996 proved the overlay is `shown`; his eyes still read an empty dark stage, and the two
        # were both honest because nothing asked where the first CARD sits inside the scroller.
        # firstCardTop >= clientH at rest means he opens THE SHELF and sees no reel at all.
        _ft, _ch = shelf.get("firstCardTop"), shelf.get("clientH")
        if (isinstance(_ft, (int, float)) and isinstance(_ch, (int, float)) and _ch > 0
                and not shelf.get("scrollTop") and _ft >= _ch):
            return MISSING, ("THE SHELF OPENS ON NOTHING — the box is real (%sx%s) and %s card(s) "
                             "are built, but the first one starts %dpx down a %dpx window, so at "
                             "rest he sees only furniture. %spx of content sits below the fold. "
                             "This is a LAYOUT fault, not a paint failure — the cards are there."
                             % (shelf.get("w"), shelf.get("h"),
                                "UNKNOWN" if cards is None else cards, _ft, _ch,
                                _said(shelf.get("belowFoldPx"))))
        return OK, ("the shelf is open and on screen (%sx%s at top %s, viewport %s) — %s card(s) "
                    "by the panel count, %s by the grid count, first card %spx into a %spx window"
                    % (shelf.get("w"), shelf.get("h"), shelf.get("top"), shelf.get("vh"),
                       "UNKNOWN" if cards is None else cards,
                       "UNKNOWN" if grid is None else grid,
                       "UNKNOWN" if _ft is None else _ft,
                       "UNKNOWN" if _ch is None else _ch))
    _n = ("an UNKNOWN number of" if cards is None else ("%d" % cards))
    _why = ("OFF-VIEW means an ancestor is display:none — the overlay generates no layout boxes "
            "at all, which is why nothing paints while the DOM is perfectly built"
            if state == "OFF-VIEW" else
            "it is laid out, but not where a reader can reach it")
    return MISSING, ("THE SHELF IS OPEN AND NOT ON SCREEN — %s, holding %s card(s) (%s by the "
                     "grid count). h=%s top=%s viewport=%s boxes=%s. %s. ⚠ This is the pair his "
                     "eyes and this beat were disagreeing about."
                     % (state, _n, "UNKNOWN" if grid is None else grid, shelf.get("h"),
                        shelf.get("top"), shelf.get("vh"), shelf.get("boxes"), _why))


def _said(n):
    """-> the number, or the word UNKNOWN. Never `or 0`.

    ⚠ `x or 0` prints "0 of 0 series frozen" and "0px sits below the fold" when the producer
    deliberately published null, turning a refusal to measure into an affirmative measurement —
    inside the very sentence declaring a fault. 0 is measured-and-zero; None is nobody looked.
    [[unknown-stays-unknown]] [[zero-needs-a-denominator]]
    """
    return "UNKNOWN" if n is None else n


def _check_the_screen_is_still_painting():
    """THE ONE CHECK THAT DOES NOT ASK THE PAGE. (#34)

    Measured on his machine 2026-09-10 from Grok Bot's captures: the TV DIABLO window was a DARK
    BLANK at 19:08 and a WHITE BLANK at 16:16 — titlebar and nothing else — while every text-based
    check reported health (`GET / 200 in 16ms - 1,744,954 bytes`, `GET /api/status 200 in 68ms`,
    "quiet hold - HEART census held - did not kill"). A page that answers 200 can paint nothing, so
    every other check in this file is blind to a dead compositor by construction. This one reads
    the BYTES of screencaptures of the real window.

    ⚠ FRESHNESS IS PART OF THE ANSWER, NOT A FOOTNOTE. A frozen pair from four hours ago is a true
    statement about four hours ago and says NOTHING about the screen now. Grok Bot captures on a
    ~10 minute loop, so once the newest frame is over an hour old nobody is watching and the honest
    verdict about NOW is UNKNOWN — with the stale finding still reported, because it is evidence.
    [[stale-reading]] [[unknown-stays-unknown]]

    ⚠ FROZEN is not BLANK. This says two captures are identical; whether the screen is empty is a
    claim about content that needs an eye on the frame.
    """
    try:
        import frozen_frame_watch as FFW
    except Exception as e:
        return UNKNOWN, ("the frozen-frame watch could not be imported (%s), so the pixels went "
                         "unread" % type(e).__name__)
    try:
        r = FFW.report()
    except Exception as e:
        return UNKNOWN, "the frozen-frame watch raised %s, so nothing was measured" % type(e).__name__

    c = r.get("counts") or {}
    if r.get("state") == FFW.UNKNOWN:
        return UNKNOWN, ("no capture of his window could be compared here (%d png(s), %d window "
                         "series). That is not a clean bill — it is nobody looking."
                         % (c.get("pngs") or 0, c.get("standing") or 0))

    STALE_S = 3600.0
    _series = [x for x in (r.get("series") or []) if isinstance(x.get("ageS"), (int, float))]
    frozen = [x for x in _series if x.get("state") == FFW.FROZEN]

    # ⚠⚠ v2998 GRADED FRESHNESS BY min(ageS) ACROSS *ALL* SERIES, so a five-hour-old freeze read as
    # a live fault whenever any other geometry had a recent capture. v3001 fixed that by taking
    # `frozen[0]` — and frozen[0] is the series with the MOST FRAMES, because report() sorts by
    # -len(rows) and never by age. Reproduced 2026-09-12: a 95-frame freeze 5h old beside a
    # 12-frame freeze 60 SECONDS old returned UNKNOWN, and the live fault this row exists for was
    # never reported. Twice now the freshness question has been answered by whichever series
    # happened to sort first. The evidence for a FAULT is the FRESHEST fault.
    # [[stale-reading]] [[feedback-suspect-the-instrument]]
    if frozen:
        f = min(frozen, key=lambda x: x.get("ageS"))
        age = f.get("ageS")
        if age > STALE_S:
            return UNKNOWN, ("the freshest frozen window series (%s) was last captured %.1fh ago, "
                             "so nothing is known about the screen NOW. %d series were frozen when "
                             "anyone last looked. Grok Bot captures on a ~10 minute loop; this old "
                             "means it is not watching."
                             % (f.get("geom"), age / 3600.0, len(frozen)))
        return MISSING, ("HIS SCREEN STOPPED PAINTING — %s is byte-identical across %.0fs (%s, "
                         "captured %.0fs ago); %d of %s comparable window series frozen. A live "
                         "console never captures twice to the same bytes. ⚠ FROZEN is measured; "
                         "BLANK is not — go look at the frame."
                         % (f.get("geom"), f.get("gapS") or 0, f.get("sha"), age, len(frozen),
                            _said(c.get("standing"))))

    # ⚠⚠ AND THE HEALTHY PATH HAD THE MIRROR OF THE SAME BUG. An OK here is a claim about EVERY
    # series, so it cannot rest on the freshest one: his console has 8 geometries, and with one
    # captured 2 minutes ago and another untouched for 5 hours, min(ageS) said 120 and the row
    # returned "8 window series compared, all painting" — a clean bill for a window nobody had
    # looked at since morning. A verdict is only as fresh as the OLDEST evidence it covers, so the
    # stale ones are excluded from the claim and COUNTED rather than quietly included.
    fresh = [x for x in _series if x.get("ageS") <= STALE_S]
    stale = [x for x in _series if x.get("ageS") > STALE_S]
    if not fresh:
        return UNKNOWN, ("every comparable window series was last captured over %.0fh ago (%d of "
                         "them), so nothing is known about the screen now"
                         % (STALE_S / 3600.0, len(stale)))
    return OK, ("%d window series compared from %s capture(s), all painting%s"
                % (len(fresh), _said(c.get("pngs")),
                   "" if not stale else
                   " — %d further series excluded, last captured over %.0fh ago and too old to "
                   "speak for now" % (len(stale), STALE_S / 3600.0)))


CHECKS = [
    # v2961 (#67) — the drift lane compares version LABELS; this compares the BYTES, which is the
    # only way an unstamped save can be seen. See the docstring for why it asks the console rather
    # than hashing its own import.
    ("running code matches disk", _check_the_running_code_is_the_code_on_disk),
    # v2942 (#59) — THE DRIVER EXISTED, WAS GATED, AND NOTHING RAN IT. See the docstring: his
    # stored beat was 31.6h old while control_app imported the module under two aliases and called
    # nothing on either. [[the-unjoined-end]]
    ("shelf lanes reading", _check_the_shelf_lanes_are_still_reading),
    # v2843 — THE FLEET, WHICH THE HEART HAD NEVER HEARD OF. `grep -c fleet` was 0 across
    # heart.py and lane_census.py while his card sat on "unreachable" and the footer said 8 dark.
    ("fleet reachable", _check_the_fleet_lane_is_reachable),
    # v2277 — four questions nobody was asking. Each was found BY HAND this session, and each was
    # silent by construction: an armed one-shot that would have dropped 273 of his 280 owned names,
    # a lane that had said nothing for 137h, a console asking ITSELF for the board, and my own
    # unbounded glob holding a core at 99.7% for 28 hours.
    ("armed migration", _health("armed_migration")),
    ("extraction lanes", _health("lanes")),
    # v2304 — the watcher that makes playing enough. It reaches the ONE surface in the same
    # breath as the lanes it belongs beside, or it is a feature only a log knows about.
    ("shadow watch", _health("shadowWatch")),
    # v2310 — the two game readers, on the one surface he reads
    ("readers agree", _health("readers")),
    ("board join", _health("board_join")),
    ("stray processes", _health("orphans")),
    # ⚠ v2228 — (NAME, FN) TUPLES. My first cut added these two as BARE FUNCTIONS and broke the
    # `for n, fn in CHECKS` unpacking in nine places at once, including the healer's recheck map.
    # THE COUNT WAS THE TELL: nine errors from one edit is a shape mistake, not nine defects.
    ("engines corroborate", _check_the_engines_CORROBORATE_each_other),
    # v2336 — the eagle can see his SCREEN, not only his engines
    ("panels on screen", _check_no_panel_is_dark_with_its_content_in_hand),
    # v2336 — the suites belong on GitHub; this notices when one comes back to his laptop
    ("test venue", _check_no_browser_suite_is_scheduled_on_this_mac),
    # v2761 — the river's ELEVEN joints reach a screen; the existing "the river" row
    # watches reel_router (WHERE reels are stationed), which is a different question.
    ("river joints", _check_the_river_joints_carry),
    # the outlet — ROUTED was unreachable while its only writer lived inside the deleter, so no
    # reel could ever be recorded as finished. This watches whether the river actually drains.
    ("river outlet", _check_the_river_has_an_outlet),
    # the accumulator's stored proposal, re-gated against today's bars. `vault stores` above asks
    # only whether the files are readable; this asks whether what they OFFER is still acceptable.
    ("vault proposal", _check_the_vault_proposal_still_clears_todays_bar),
    ("console UI faults", _check_the_console_UI_has_not_faulted),
    ("version drift", _check_version_drift),
    # v2248 — the OTHER out-of-sync: drift is process-vs-disk, this is disk-vs-origin, and
    # Dean sat 85 versions behind with drift green because his two agreed on old bytes.
    ("behind the fleet", _check_behind_the_fleet),
    ("lane intent", _check_lane_intent),
    ("what runs without you", _check_what_runs_without_him),
    ("disk headroom", _check_disk_headroom),
    ("subscription", _check_subscription_burn),
    ("unattended reel", _check_a_reel_is_not_recording_unattended),
    ("reel extract", _check_the_reel_extract_is_moving),
    ("hunt economy", _check_the_hunt_is_buying_something),
    ("sweep would find", _check_the_sweep_would_find_something),
    ("board is claimed", _check_the_board_world_is_claimed),
    # v2746 — WHERE each ledger's rows came from, per ledger. `board is claimed` above asks whether
    # this world PERSISTS; this asks whether its rows are its OWN. Different sentences, and the
    # second was answered by one boolean over three ledgers until now.
    ("ledger provenance", _check_every_ledger_can_say_WHERE_IT_CAME_FROM),
    # v2746 — the GENERAL form of the seed defect. `ledger provenance` asks WHERE a figure came
    # from; this asks HOW OLD it is, for every ledger figure and not only the seeds. His words:
    # "connect it all to the heart of the console so nothing becomes stale again".
    ("ledger staleness", _check_no_ledger_FIGURE_has_gone_stale_unnoticed),
    ("visual lock", _check_the_visual_lock_holds),
    ("art corpus", _check_the_art_corpus),
    ("footage has a reel", _check_footage_belongs_to_a_reel),
    ("vault stores", _check_the_vault_stores_are_readable),
    # v2730 — his "so its all not in the dark": the evidence ledger and the backup that is meant
    # to protect it both had ZERO rows in this list until now.
    ("evidence ledger", _check_the_evidence_ledger_is_readable),
    ("ledger backup", _check_the_ledger_backup_covers_every_store),
    ("backup loop", _check_the_backup_loop_is_actually_WRITING),
    ("console painted whole", _check_the_console_painted_all_of_itself),
    ("names banked", _check_read_names_are_actually_banked),
    ("read names lane", _check_read_names_lane),
    ("stage shows the dom", _check_the_stage_shows_what_the_dom_claims),
    ("river walk", _check_the_river_walk_is_walking),
    # v#### — ONE ROW PER REEL ROUTE. ⚠ THE NAMES ARE HARD-CODED ON PURPOSE, so they are
    # greppable and so the rail cannot silently grow a row nobody argued for; the gate asserts
    # this list covers every entry in reel_templates.ROUTES, which is where a fifth route would
    # otherwise arrive unwatched. [[the-unjoined-end]]
    ("route stash", _route_health("stash")),
    ("route chronicle · sets", _route_health("chronicle · sets")),
    ("route chronicle · uniques", _route_health("chronicle · uniques")),
    ("route inventory", _route_health("inventory")),
    ("printer reach", _check_the_printer_can_reach_the_corpus),
    ("end routes reachable", _check_every_reel_can_still_reach_an_end_route),
    ("the river", _check_the_river_is_moving),
    # v2995 (#34) — THE ONLY CHECK THAT DOES NOT ASK THE PAGE. Every other entry in this list can
    # be answered 200 by a console that is painting nothing; measured on his machine 2026-09-10,
    # that is exactly what happened twice in one day. This one hashes screencaptures of the real
    # window. [[the-blank-console-detector]]
    ("screen still painting", _check_the_screen_is_still_painting),
    # v2996 (#58/#34) — THE FILL AND THE RECT, TOGETHER. Grokbot saw an empty stage while this
    # same beat reported cards~535; both were honest, because a DOM can be built inside a
    # container that occupies no pixels and nothing ever asked WHERE it was. [[the-unjoined-end]]
    ("shelf is where it says", _check_the_shelf_is_where_it_says_it_is),
    ("progress number", _check_his_progress_number_has_not_been_overwritten),
    ("ledger entries", _check_no_ledger_ENTRY_has_silently_vanished),
    ("store emptied", _check_the_board_store_did_not_come_up_empty),
    ("shadow gate", _check_the_shadow_gate_is_learning),
    ("locked lanes", _check_the_locked_lanes_still_refuse),
    ("his gear", _check_his_gear_is_being_learned),
    ("tooltip finder", _check_the_tooltip_finder_is_honest),
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
# v2801 — AND "engines corroborate" WAS NEVER CHEAP EITHER. The exact same defect as the line
# above, found the same way: by timing the members rather than trusting the list. Measured
# 2026-09-08 across fresh processes: **7,672 ms · 6,638 ms · 7,692 ms**, and 13,038 ms inside a
# test process — against a subset budget of 3,000 ms per check. It was the largest single cost in
# the "cheap" set every time it was the largest cost in anything.
#
# ⚠ THE REASON IT HID FOR SO LONG IS WORTH MORE THAN THE FIX. The cheap-subset gate names its
# culprits, and the name it printed CHANGED EVERY RUN — 'stage shows the dom (7301 ms)' once,
# 'armed migration (3645 ms)' and 'panels on screen (3384 ms)' the next, 141 ms each minutes later.
# Attention went to whichever name was printed, and each of those was innocent: re-timed on the
# spot they cost 75-146 ms. The one check that was slow in EVERY reading was rarely the one
# accused, because a burst on a busy machine lands wherever it lands. A flapping gate does not
# merely fail to catch a defect - it actively points away from it.
# [[feedback-suspect-the-instrument]] [[regression-guard]]
#
# It stays on the roster and the full doctor run still performs it (the mirror gate
# test_a_check_moved_to_SLOW_is_still_RUN_somewhere enforces exactly that); it simply stops
# running on the ten-minute timer and in the boot path of every console a test spawns.
# ⚠ v3014 — "sweep would find" LEFT SLOW FOR PERIODIC. SLOW means NEVER RUNS UNATTENDED
# (_eagle_once calls include_slow=False), so the one sweep-shaped eagle check ran only when a
# human pressed the button — the census named it the #3 organ gap. Cost, both figures honest:
# 16,585 ms once measured on a full shelf (why it went to SLOW), 1,660 ms measured 2026-09-12 on
# today's 24-reel shelf. At PERIODIC's ~hourly unattended cadence either figure is the same class
# as 'engines corroborate' (6,638-13,038 ms), which is the precedent tier for exactly this shape.
SLOW = ("the other doctors",)

# ══ v2802 — A THIRD TIER, AND THE REASON IS A REGRESSION I SHIPPED YESTERDAY ══════════════════
# v2801 measured `engines corroborate` at 6,638-13,038 ms in the CHEAP subset and moved it into
# SLOW. The cost was real and the move was wrong, and a cross-family review of the pushed diff is
# what said so: `_eagle_once` calls `run(include_slow=False)`, so SLOW does not mean "runs less
# often" — it means **NEVER RUNS UNATTENDED**. That check is the sole caller of
# `corroborate.verdict()`, which holds every cross-engine invariant there is: owned-is-contained,
# chronicle-owed, swept-split-adds-up, evidence-survived-its-sweep. A 19-vs-2 or 1263-vs-403
# disagreement would have stopped being detected by anything except him pressing the eagle button.
#
# ⚠ THE MIRROR GATE PASSED THE WHOLE TIME. `test_a_check_moved_to_SLOW_is_still_RUN_somewhere`
# asks whether the FULL run still performs it — it does — and that question cannot see the thing
# that was removed, which is the SUPERVISION LOOP. "Runs somewhere" and "runs unwatched" are
# different properties and only one of them was guarded. [[build-the-heart-and-census-everywhere]]
#
# So: SLOW keeps its meaning (on demand only, ~2 minutes, a human is waiting). PERIODIC is the
# honest tier for a check that is too expensive for every ten-minute tick and too important to go
# unwatched — it runs unattended on a longer cadence instead of not at all.
PERIODIC = ("engines corroborate", "sweep would find")
PERIODIC_EVERY = 6      # eagle ticks. The eagle sleeps ~10 min, so this is roughly hourly.


def _slow_path():
    env = os.environ.get("TV_EAGLE_SLOW")
    if env:
        return env
    return os.path.join(HERE, ".eagle_slow.json")


def _load_slow():
    """-> dict | None. None is UNKNOWN. {} is measured-empty (no sidecar yet).

    A missing sidecar is NEVER (no full pass stored). A file that exists and will not
    parse is None — slow_surface still paints NEVER, and must not look like a stored pass.
    """
    p = _slow_path()
    if not os.path.exists(p):
        return {}
    try:
        with open(p, encoding="utf-8") as fh:
            d = json.load(fh)
        return d if isinstance(d, dict) else None
    except Exception:
        return None


def _persist_slow(rows):
    """CF-12 — the two SLOW checks reach a durable sidecar, not the cheap pass.

    Joining them INTO `run(include_slow=False)` would make that pass emit 34 rows, and
    eagle-ran-every-check (which expects 32 on a labelled cheap pass) would go permanently
    red again — the exact alarm he photographed. Persist here; `slow_surface()` is the tap.
    """
    blob = {"at": int(time.time() * 1000),
            "rows": [dict(r) for r in (rows or []) if r.get("check") in SLOW]}
    p = _slow_path()
    tmp = p + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(blob, fh, indent=1, sort_keys=True)
        os.replace(tmp, p)
    except Exception:
        try:
            os.remove(tmp)
        except Exception:
            pass


def slow_surface(now_ms=None):
    """The two checks the timer never runs, last-known or NEVER. Always len(SLOW) rows.

    Tradeoff: they are not live on the 10-minute pass. They are last-known-with-age, or
    UNMEASURED if no full pass has ever been stored. The cheap `run()` row count stays
    len(CHECKS)-len(SLOW).
    """
    now = int(now_ms if now_ms is not None else time.time() * 1000)
    persist = _load_slow()
    if not isinstance(persist, dict):
        persist = {}
    by = {r.get("check"): r for r in (persist.get("rows") or []) if isinstance(r, dict)}
    at = persist.get("at")
    out = []
    for name in SLOW:
        prev = by.get(name)
        if not prev:
            out.append({
                "check": name, "state": UNMEASURED,
                "why": ("not in the unattended pass (SLOW; ~2 min). never stored from a full "
                        "pass. NEVER, not missing."),
            })
            continue
        age = "UNKNOWN"
        try:
            import unknown_age as _ua
            age = _ua.age_say(at, now)
        except Exception:
            pass
        out.append({
            "check": name,
            "state": prev.get("state"),
            "why": (prev.get("why") or "") + " · last full pass %s ago" % age,
            "lastFullPassTs": at,
        })
    return out


@contextlib.contextmanager
def tick_caches():
    """Prime the per-tick caches exactly as a production tick does, then reset them. -> None

    ⚠⚠ v2815 — THE TIMING GATE WAS MEASURING THE BRANCH THE CONSOLE NEVER TAKES.
    `run()` is the ONLY caller of a check in production, and before iterating CHECKS it primes
    three caches. So `_board_read()` in production ALWAYS returns the cached value:

        if _board_cache["active"]:            <- production: always True, inside run()
            return _board_cache["got"]
        return _post("/api/board_ownership", ...)   <- the gate: always THIS one

    `test_the_cheap_subset_is_actually_CHEAP` calls each check directly and never sets `active`,
    so it exercised the uncached branch exclusively. Roughly 9-15 of ~34 checks read through these
    caches (_board_read ~5, _health_report ~6, _route_read ~4). Break the cached line and every
    real watchdog tick would feed None into five checks forever while the gate stayed green — the
    broken line is simply never executed under test.

    ★ WHY THIS IS A CONTEXT MANAGER AND NOT "MAKE THE GATE CALL run()". run()'s own comment states
    the constraint: "Opened HERE and nowhere else, so a check called on its own still reads fresh —
    which is what every guard that stubs _post expects, and what my first cut broke eight of."
    Calling checks BARE is deliberate and eight guards depend on it. So the priming becomes
    shareable rather than moving, and only the gate that measures TIMING opts in — because timing
    is the one question whose answer differs between the two branches.
    [[feedback-blind-fixture-green-gate]] [[gate-blind-to-unexercised-input]]
    """
    _board_cache["active"], _board_cache["got"] = True, _post("/api/board_ownership", {"sample": 0})
    _health_cache["active"], _health_cache["rep"] = True, None
    _routes_cache["active"], _routes_cache["got"] = True, _route_census_once()
    try:
        yield
    finally:
        _board_cache["active"], _board_cache["got"] = False, None
        _health_cache["active"], _health_cache["rep"] = False, None
        _routes_cache["active"], _routes_cache["got"] = False, None


def run(include_slow=True, include_periodic=None):
    """-> rows. `include_periodic` defaults to `include_slow` so every existing caller keeps its
    exact behaviour; the eagle passes it explicitly on its own cadence."""
    if include_periodic is None:
        include_periodic = include_slow
    rows = []
    # v2277 — ONE TICK, ONE READ OF HIS BOARD. Three checks need /api/board_ownership and that
    # route EVALUATES JAVASCRIPT IN THE WINDOW HE IS LOOKING AT; asking three times buys nothing.
    # Opened HERE and nowhere else, so a check called on its own still reads fresh — which is what
    # every guard that stubs _post expects, and what my first cut broke eight of.
    # v2815 — THROUGH tick_caches(), so the gate that measures this tick's cost can prime it the
    # same way instead of timing a different branch. One source; a divergence is now impossible
    # rather than merely unlikely.
    with tick_caches():
        for name, fn in CHECKS:
            if not include_slow and name in SLOW:
                continue
            if not include_periodic and name in PERIODIC:
                continue
            try:
                state, why = fn()
            except Exception as e:
                state, why = UNKNOWN, "this check itself threw: %s" % str(e)[:120]
            rows.append({"check": name, "state": state, "why": why})
    if include_slow:
        _persist_slow(rows)
    try:
        import unknown_age as _ua
        _ua.attach(rows)
    except Exception:
        pass
    return rows


def report(deep=False):
    """The organ interface — what this doctor WATCHES. -> {"ok", "rows", "why"}

    Every other organ publishes one of these (`health_engine.report()`,
    `control_app.eagle_state()`), and until v2496 this one did not, so `organ_matrix` answered
    "console_doctor has no report()" and painted the doctor's column UNKNOWN across all 44
    surfaces — a quarter of that table unanswerable because one function was absent.

    ⚠⚠ IT DOES NOT RUN THE CHECKS BY DEFAULT, AND THAT IS THE DESIGN, NOT A SHORTCUT.
    `run()` opens /api/board_ownership, and that route EVALUATES JAVASCRIPT IN THE WINDOW HE IS
    LOOKING AT [[borrowed-surface]]; the two SLOW checks add ~2 minutes on top. An organ asked
    "what do you watch?" must be able to answer without reaching into his screen, because the
    asker — a matrix, the heart, a status poll — is asking about COVERAGE, not about findings.
    Pass deep=True when you want the live states; that is `run()`, and it answers a different
    question.

    So every row here carries state UNMEASURED, which is a real state in this module's own
    vocabulary and NOT a pass: it says this check exists and was not run just now.
    [[unknown-stays-unknown]] — the gap between "we did not look" and "we looked and it was
    fine" is the whole point of having a separate word for it.
    """
    if deep:
        rows = run()
        return {"ok": True, "rows": rows,
                "why": "%d check(s), run live just now" % len(rows)}
    rows = []
    for name, _fn in CHECKS:
        rows.append({
            # ⚠ `check` IS THIS MODULE'S WORD AND IT STAYS. The matrix learned to read it
            # (v2496) rather than this file learning to speak someone else's vocabulary — a
            # synonym list belongs in the READER, or every organ ends up carrying a second
            # copy of its own name for each consumer. [[copy-drift]] §1
            "check": name,
            "slow": name in SLOW,
            "owner": owner_of(name),
            "state": UNMEASURED,
            "why": ("named by this doctor; not run by this call. UNMEASURED, not OK — "
                    "pass deep=True to run it."),
        })
    return {"ok": True, "rows": rows,
            "why": ("%d check(s) named without running any of them, because running them "
                    "reaches into the window he is looking at" % len(rows))}


def main(argv):
    rows = run()
    if "--json" in argv:
        print(json.dumps({"ok": True, "checks": rows,
                          "generatedTs": int(time.time() * 1000)}, ensure_ascii=False))
        return 0
    print("\n🦅 EAGLE EYE — the whole console, from above\n")
    for r in rows:
        print("  %s %-18s %s" % (ICON.get(r["state"], "⚪"), r["check"], r["why"]))
    # v2284 — split by OWNER before counting. His number must mean "things you can do".
    needs = [r for r in rows if r["state"] == MISSING and owner_of(r["check"]) == "you"]
    mine = [r for r in rows if r["state"] == MISSING and owner_of(r["check"]) == "me"]
    unk = [r for r in rows if r["state"] == UNKNOWN]
    print()
    if needs:
        print("⚠ %d thing(s) need you. Nothing above is a guess: each line names what it measured."
              % len(needs))
    if mine:
        # ⚠ SHOWN, NOT SWALLOWED. These are real and red; they are simply not his to do, and each
        # one names the task that owns it so "mine" cannot become a place things go to be forgotten.
        print("🔧 %d known defect(s) — mine, already queued, not yours to do:" % len(mine))
        for r in mine:
            print("     %-18s %s" % (r["check"], MINE.get(r["check"], "")))
    if needs or mine:
        pass
    elif unk:
        print("✅ nothing is out of line. %d check(s) could not be determined — that is not a pass, "
              "it is a gap." % len(unk))
    else:
        print("✅ every check green.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
