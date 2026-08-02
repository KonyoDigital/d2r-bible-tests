#!/usr/bin/env python3
"""Survey + recover sealed reels whose index.json went missing. HAND-RUN, DRY BY DEFAULT.

WHY THIS EXISTS
    A sealed reel is a directory of f_<epoch-ms>.jpg frames plus ONE index.json. Everything that
    plays a reel back — theatre, chronicle_retro.read_reel(), sweep_hist() — opens index.json first
    and gives up with note="no-index" when it is not there. The frames can all be perfect and the
    reel is still a black screen. That is exactly what happened to the 98-frame session sealed at
    01:04 tonight: 98 real JPGs on disk, no index, unplayable.

    The seal path wrote the index only AFTER a per-frame blank-detection pass that DECODES every
    JPEG, and wrapped the whole thing in a swallowing `except Exception`. On 98 frames that pass is
    long enough for the shutdown kill to land inside it, so the cheap artefact the reel cannot live
    without was lost to an expensive one it can. SEAL-2 fixes the order and the swallow; this file
    is the mop for reels that already lost theirs.

RECONSTRUCTION IS EXACT, NOT A GUESS
    An index row is {"f": <name>, "ts": int(<name>[2:-4])} — every byte of it already lives in the
    filename. Rebuilding from the directory listing recovers the same rows the seal would have
    written. The rebuild itself belongs to reel_index.ensure_reel_index(); this module IMPORTS
    it and never re-implements it, so there is exactly one writer of an index in the repo.

BLANK FLAGS ARE **NOT** RECONSTRUCTED — DELIBERATELY
    A rebuilt index carries no "blank": true rows. Three reasons, in order of weight:
      1. HONESTY. A blank flag makes a sweep skip a frame. Guessing one — or copying a neighbour's —
         can hide real footage from him permanently, and he would never see the frame that was
         dropped. A missing flag costs compute; a wrong flag costs evidence.
      2. COST. Decoding a frame to measure flatness is 0.076 s/frame (measured on his real 98-frame
         reel: ~7.5 s for the reel). That per-frame decode pass is the exact expense that lost the
         index in the first place. Recovery must not re-enter the trap it is cleaning up after.
      3. IT IS AN OPTIMISATION, NOT DATA. is_dead_frame() is re-derivable from the JPEG at any time.
         The rebuilt index is stamped with a "rebuilt" marker by ensure_reel_index(), so a later
         sweep can tell a rebuilt index from a sealed one and enrich it lazily, offline, when
         nothing is being killed.

USAGE
    python3 tv/reel_repair.py                 # dry-run survey of tv/frames/hist — writes NOTHING
    python3 tv/reel_repair.py --hist DIR      # survey some other archive
    python3 tv/reel_repair.py --apply         # write missing indexes only; idempotent

SAFETY RAILS (this runs over his real farming footage)
    * Frames are never modified, renamed or deleted. Nothing is ever deleted.
    * An index.json that EXISTS AND PARSES is never overwritten — it is skipped and said so.
    * Only directories whose basename starts with "reel_" are considered at all. tv/frames/hist also
      holds cache1280/ and cache160/, which are THUMBNAIL CACHES full of f_*.jpg and legitimately
      have no index. They are neither touched nor counted nor flagged.
    * A reel with a live index.json.tmp is being sealed right now; it is skipped rather than raced.
"""

# v1608.1 — ENCODING-SAFE BEFORE IT PRINTS ANYTHING (REG-044/054/077/078). This file prints
# emoji, and on a non-UTF-8 console (Konyo has two Windows machines) an emoji print raises
# UnicodeEncodeError — so the repair tool for a silent-failure bug would itself die while
# REPORTING, turning a clean archive into a non-zero exit. Caught by test_control's
# TestToolsCanReportTheirVerdict, which is the gate that exists for exactly this.
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
try:
    from console_safe import enable as _console_safe
    _console_safe()
except Exception:
    pass

import argparse
import json
import os
import re
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import chronicle_retro as _cr  # noqa: E402
try:
    import reel_index as _ri  # noqa: E402  (v1608 — the writer moved out of the read-only module)
except Exception:
    _ri = None

FRAME_RE = re.compile(r"^f_\d+\.jpg$")
DEFAULT_HIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frames", "hist")

# What the dry-run decided about a reel. The apply pass acts on REPAIR rows and nothing else.
OK = "ok"              # index present and parseable — leave it alone
THIN = "thin"          # index present and parseable but lists <= 2 frames — reported, NOT touched
REPAIR = "repair"      # frames on disk, no usable index — the one case --apply writes
CORRUPT = "corrupt"    # index.json present but does not parse — repairable, old file preserved
EMPTY = "empty"        # no frames and no index — nothing recoverable, nothing to do
SEALING = "sealing"    # index.json.tmp present — the agent is mid-seal, do not race it

THIN_FRAMES = 2


def frame_names(reel_dir):
    """Every f_<epoch-ms>.jpg in the dir, sorted by name (== sorted by timestamp, fixed width)."""
    try:
        return sorted(n for n in os.listdir(reel_dir) if FRAME_RE.match(n))
    except OSError:
        return []


def read_index(reel_dir):
    """(exists, listed_frames) for the reel's index.json. listed_frames is None when unparseable.

    A dict index is the v1510 shape {"sessionId", "n", "frames": [ … ]}. A bare list is accepted as
    the frame list itself so an older archive is never mislabelled corrupt and rewritten.
    """
    path = os.path.join(reel_dir, "index.json")
    if not os.path.isfile(path):
        return False, None
    try:
        with open(path, encoding="utf-8") as fh:
            idx = json.load(fh)
    except Exception:
        return True, None
    if isinstance(idx, dict):
        rows = idx.get("frames")
        if isinstance(rows, list):
            return True, len(rows)
        n = idx.get("n")
        return True, (int(n) if isinstance(n, int) else 0)
    if isinstance(idx, list):
        return True, len(idx)
    return True, None


def inspect(reel_dir):
    """Classify ONE reel dir. Pure read — opens nothing but index.json, decodes no JPEG."""
    row = {"reel": os.path.basename(reel_dir), "dir": reel_dir,
           "jpgs": len(frame_names(reel_dir)), "listed": None}
    if os.path.exists(os.path.join(reel_dir, "index.json.tmp")):
        row["state"] = SEALING
        return row
    exists, listed = read_index(reel_dir)
    row["listed"] = listed
    if exists and listed is None:
        row["state"] = CORRUPT if row["jpgs"] else EMPTY
    elif exists:
        row["state"] = THIN if listed <= THIN_FRAMES else OK
    elif row["jpgs"]:
        row["state"] = REPAIR
    else:
        row["state"] = EMPTY
    return row


def survey(hist_dir):
    """Every reel_* dir under hist_dir, oldest first. Non-reel dirs (the caches) never appear."""
    try:
        names = sorted(os.listdir(hist_dir))
    except OSError as exc:
        raise SystemExit("reel_repair: cannot read %s (%s)" % (hist_dir, exc))
    return [inspect(os.path.join(hist_dir, n)) for n in names
            if n.startswith("reel_") and os.path.isdir(os.path.join(hist_dir, n))]


VERDICT = {
    OK: "index ok",
    THIN: "index ok (thin: <= %d frames)" % THIN_FRAMES,
    REPAIR: "%s index.json from filenames",
    CORRUPT: "%s (index.json does not parse; old file kept as .bad-<epoch>)",
    EMPTY: "nothing to recover (no frames)",
    SEALING: "SKIP — index.json.tmp present, a seal is in flight",
}

# What the index: column says. An EMPTY reel has no index either, but there is nothing to rebuild
# from, so it must not read "ok" — that is the one wording that could make a real gap look handled.
INDEX_COL = {REPAIR: "MISSING", CORRUPT: "unparseable", SEALING: "in-flight", EMPTY: "none"}


def repair(row):
    """Write a reconstructed index for ONE reel. Returns True when this call wrote one.

    The reconstruction itself is reel_index.ensure_reel_index() — imported, never re-written
    here. It is the atomic writer (tmp + fsync + os.replace) and the one place the "rebuilt" marker
    is stamped, and it is a no-op when a usable index is already there, which is what makes a second
    --apply run idempotent even if this module's own view of the dir went stale.
    """
    if row["state"] == CORRUPT:
        # Additive: the unparseable file is preserved, never dropped, before the writer replaces it.
        bad = os.path.join(row["dir"], "index.json")
        try:
            shutil.copy2(bad, bad + ".bad-%d" % int(time.time()))
        except OSError as exc:
            print("  ! %s: could not preserve the corrupt index (%s) — SKIPPED" % (row["reel"], exc))
            return False
        try:
            os.remove(bad)  # the copy above is the backup; ensure_reel_index() must see no index
        except OSError as exc:
            print("  ! %s: could not clear the corrupt index (%s) — SKIPPED" % (row["reel"], exc))
            return False
    try:
        _ri.ensure_reel_index(row["dir"])
    except Exception as exc:  # LOUD. The whole bug being cleaned up here was a swallowed failure.
        print("  ! %s: rebuild FAILED (%s: %s)" % (row["reel"], type(exc).__name__, exc))
        return False
    exists, listed = read_index(row["dir"])
    if not exists or listed is None:
        print("  ! %s: rebuild produced no readable index — STILL BROKEN" % row["reel"])
        return False
    print("  + %s: rebuilt index.json — %d frames" % (row["reel"], listed))
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Survey sealed reels and rebuild any index.json that went missing. "
                    "Dry-run by default: without --apply nothing is written.")
    ap.add_argument("--hist", default=DEFAULT_HIST,
                    help="archive dir holding the reel_* dirs (default: tv/frames/hist)")
    ap.add_argument("--apply", action="store_true",
                    help="actually write a reconstructed index into reels that have frames but no "
                         "usable index. Never overwrites an index that parses.")
    args = ap.parse_args(argv)

    hist = os.path.abspath(args.hist)
    rows = survey(hist)
    print("reel_repair — %s%s" % (hist, "" if args.apply else "   [DRY RUN — writes nothing]"))
    print("")
    if not rows:
        print("  (no reel_* dirs found)")
        return 0

    width = max(len(r["reel"]) for r in rows)
    verb = "REBUILDING" if args.apply else "WOULD REBUILD"
    for row in rows:
        listed = "-" if row["listed"] is None else str(row["listed"])
        note = VERDICT[row["state"]]
        print("  %-*s  %4d jpg  index:%-12s listed:%-5s  %s" % (
            width, row["reel"], row["jpgs"], INDEX_COL.get(row["state"], "ok"),
            listed, (note % verb) if "%s" in note else note))

    todo = [r for r in rows if r["state"] in (REPAIR, CORRUPT)]
    thin = [r for r in rows if r["state"] == THIN]
    print("")
    print("  reels total ................. %d" % len(rows))
    print("  missing/unusable index ...... %d%s" % (
        len(todo), (" -> " + ", ".join(r["reel"] for r in todo)) if todo else ""))
    print("  index lists <= %d frames ..... %d%s" % (
        THIN_FRAMES, len(thin), (" -> " + ", ".join(r["reel"] for r in thin)) if thin else ""))
    frames = sum(r["jpgs"] for r in rows)
    lost = sum(r["jpgs"] for r in todo)
    print("  frames archived ............. %d  (%d in reels that cannot play%s)" % (
        frames, lost, "" if not frames else ", %.0f%%" % (100.0 * lost / frames)))

    if not args.apply:
        print("")
        print("  dry run — nothing written. Re-run with --apply to rebuild the %d missing index%s."
              % (len(todo), "" if len(todo) == 1 else "es") if todo
              else "  dry run — every reel already has a usable index. Nothing to repair.")
        return 0

    if not hasattr(_ri, "ensure_reel_index"):
        # The rebuild lives in ONE place on purpose. If it is not there, say so and write nothing —
        # a half-invented index would be worse than the missing one it replaced.
        print("")
        print("  !! reel_index.ensure_reel_index() is missing — cannot rebuild. NOTHING WRITTEN.")
        print("     (this module is a wrapper; it does not carry its own reconstruction on purpose)")
        return 2

    print("")
    if not todo:
        print("  --apply: nothing to do, every reel already has a usable index.")
        return 0
    fixed = sum(1 for row in todo if repair(row))
    print("")
    print("  repaired %d of %d." % (fixed, len(todo)))
    return 0 if fixed == len(todo) else 1


if __name__ == "__main__":
    sys.exit(main())
