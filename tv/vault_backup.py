#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""THE VAULT'S OWN TIMESTAMPED SAVE — separate from the chronicles, because he said so.

Konyo, 2026-09-13: *"its fine i want it zeroed and able to be brought back based on like last
recent save ledger wise... by day and timestamp ... but vault is separate and it can be restored or
wiped clean with a safeguarded button that asks twice"*.

⚠⚠ THIS IS NOT A SECOND COPY OF THE LEDGER BACKUP, AND THE DIFFERENCE IS REAL. `_ledger_snapshot_once`
(control_app.py:19997) snapshots his CHRONICLES — foundLog, owned, setPieces, gameFound, rwMade —
by asking `board_ownership()`, because that data lives in the board's own store and only the board
can read it. The VAULT is six JSON FILES on this disk. One is a browser store read over a wire, the
other is a directory; a single mechanism covering both would have to fake half of what it does.
His own words draw the same line: *"the chronicles are built in to the profile by ledger... but
vault is separate"*.

⚠ WHAT IS REUSED, DELIBERATELY: the retention SHAPE that `_ledger_backup_prune` earned the hard way
in v3009 (#81) — everything younger than 48h kept, the first save of each UTC day kept 90 days,
because his 2026-09-08 loss was noticed three days late and the oldest backup on disk was 69 HOURS
too young to answer "which save predates this". That policy was sized from a real loss and is not
re-derived here. What is NOT reused is its episode guard, which reads `d2r_storeEmptied` out of a
board snapshot and has no meaning for a directory of vault files.

⚠⚠ NOTHING HERE DELETES A VAULT STORE. This module only ever COPIES. The wipe he asked for is a
separate, twice-asking act, and a backup module that can also destroy is one bug away from being
the thing it was built to protect against.
"""
import glob
import io
import os
import shutil
import time

# ⚠ REG-044 — THIS FILE PRINTS NON-ASCII, AND A TOOL THAT CRASHES WHILE REPORTING IS WORSE THAN ONE
# THAT NEVER RAN. On a non-UTF-8 console (his Windows box prints cp1255) the arrows and warning
# glyphs below would raise mid-`print`, turning a clean verdict into a traceback and a passing tree
# into a non-zero exit. test_every_cli_that_prints_non_ascii_is_encoding_safe caught this on the
# push that would have shipped it.
try:
    from console_safe import enable as _console_safe_enable
    _console_safe_enable()
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
BACKUP_DIR = os.path.join(os.path.expanduser("~"), "d2r_vault_backups")

# ⚠ NAMED, NOT GLOBBED. A glob for vault*.json would sweep in whatever a future feature happens to
# call vault-something, and a backup whose contents drift is one nobody can reason about restoring.
# Each of these is a store with a declared owner in store_owners.py.
STORES = (
    "vault_accum.json",          # what the vault sweep accumulated per reel   (vault_retro)
    "vault_swept.json",          # the seal store — which sessions are done    (frame_authority)
    "vault_seen.json",           # what has been seen
    "vault_corpus_index.json",   # which frames of which reels show a surface
    "vault_last_result.json",    # the last sweep's result
    ".vault_autoread.json",      # the autoread lane's own state
)

KEEP_RECENT_H = 48               # the rolling window, from _ledger_backup_prune's measured policy
KEEP_DAILY_DAYS = 90             # one keeper per UTC day


def present(here=None):
    """Which stores exist right now. -> [(name, bytes)] — absence is reported, never assumed empty."""
    here = here or HERE
    out = []
    for n in STORES:
        p = os.path.join(here, n)
        out.append((n, os.path.getsize(p) if os.path.exists(p) else None))
    return out


def save(here=None, stamp=None):
    """Copy every present store into one timestamped folder. -> (path, {name: bytes}) or (None, why)

    ⚠ VERIFIED AFTER WRITING. A backup nobody read back is a promise, not a safety net — and this
    one exists so a wipe can be undone, which is the worst possible moment to discover an empty
    file. Any store that does not read back at its source size fails the whole save, because a
    PARTIAL vault backup restored later would look complete and be silently short.
    """
    here = here or HERE
    have = [(n, s) for n, s in present(here) if s is not None]
    if not have:
        return None, "no vault store exists at %s — there is nothing to save" % here
    stamp = stamp or time.strftime("%Y-%m-%d_%H%M%S", time.gmtime())
    dest = os.path.join(BACKUP_DIR, stamp)
    try:
        os.makedirs(dest, exist_ok=True)
    except OSError as exc:
        return None, "could not make %s (%s)" % (dest, exc)
    wrote = {}
    for name, size in have:
        src = os.path.join(here, name)
        dst = os.path.join(dest, name)
        try:
            shutil.copyfile(src, dst)
            back = os.path.getsize(dst)
        except Exception as exc:
            return None, "%s did not copy (%s: %s) — the save is INCOMPLETE and was not kept" % (
                name, type(exc).__name__, exc)
        if back != size:
            return None, ("%s read back %d bytes against %d at the source — refusing to keep a "
                          "partial vault save, which would restore as a complete-looking short one"
                          % (name, back, size))
        wrote[name] = back
    return dest, wrote


def saves():
    """Every save on disk, newest first. -> [(path, epoch_seconds)]"""
    out = []
    for d in glob.glob(os.path.join(BACKUP_DIR, "*")):
        if not os.path.isdir(d):
            continue
        try:
            t = time.mktime(time.strptime(os.path.basename(d), "%Y-%m-%d_%H%M%S"))
        except ValueError:
            continue                      # an unparseable name is not ours to judge or delete
        out.append((d, t))
    out.sort(key=lambda r: r[1], reverse=True)
    return out


def plan_prune(now=None):
    """Which saves retention WOULD drop. -> dict. WRITES NOTHING.

    The policy is _ledger_backup_prune's, measured from his 2026-09-08 loss: keep everything inside
    48h, keep the first save of each UTC day for 90 days, drop the rest. An unparseable folder name
    is KEPT and reported rather than guessed at.
    """
    now = now or time.time()
    all_saves = saves()
    keep, drop, daily = [], [], set()
    for path, t in all_saves:
        age_h = (now - t) / 3600.0
        day = time.strftime("%Y-%m-%d", time.gmtime(t))
        if age_h <= KEEP_RECENT_H:
            keep.append({"path": path, "why": "inside the %dh rolling window" % KEEP_RECENT_H})
        elif day not in daily and age_h <= KEEP_DAILY_DAYS * 24:
            daily.add(day)
            keep.append({"path": path, "why": "first save of %s — the daily keeper" % day})
        else:
            drop.append({"path": path, "why": "older than %dh and not a daily keeper" % KEEP_RECENT_H})
    return {"ok": True, "saves": len(all_saves), "keep": keep, "drop": drop,
            "say": "%d save(s): %d kept, %d prunable. NOTHING was written."
                   % (len(all_saves), len(keep), len(drop))}


def main(argv=None):
    import sys
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--save" in argv:
        where, what = save()
        if where is None:
            print("refused: %s" % what)
            return 1
        print("saved %d store(s) to %s" % (len(what), where))
        for n, b in sorted(what.items()):
            print("   %-26s %8d bytes" % (n, b))
        return 0
    for n, s in present():
        print("  %-26s %s" % (n, ("%d bytes" % s) if s is not None else "ABSENT"))
    p = plan_prune()
    print(p["say"])
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
