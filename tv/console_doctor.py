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
    if not got.get("ok"):
        return UNKNOWN, "the board refused the read: %s" % str(got.get("why"))[:90]
    if "owner" not in got:
        # v2044 added the field. An older console cannot answer, and MUST NOT read as a pass.
        return UNKNOWN, ("this console predates the ownership field (v2044) — restart it to find "
                         "out whether the board world persists")
    counts = got.get("counts") or {}
    total = sum(int(counts.get(k) or 0) for k in ("foundLog", "owned", "setPieces"))
    if got.get("owner"):
        return OK, "the board is CLAIMED — it writes the bare keys, so what is applied persists"
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


CHECKS = [
    ("version drift", _check_version_drift),
    ("lane intent", _check_lane_intent),
    ("disk headroom", _check_disk_headroom),
    ("subscription", _check_subscription_burn),
    ("unattended reel", _check_a_reel_is_not_recording_unattended),
    ("sweep would find", _check_the_sweep_would_find_something),
    ("board is claimed", _check_the_board_world_is_claimed),
    ("the other doctors", _check_the_other_doctors),
]


# v2026 — the sub-doctor call shells out to two full diagnostics and costs ~2 minutes. That is
# fine for a human pressing the button and NOT fine on every CI run, so callers can ask for the
# cheap subset. The slow one is named rather than guessed at, so adding a check never silently
# joins the slow set.
SLOW = ("the other doctors",)


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
