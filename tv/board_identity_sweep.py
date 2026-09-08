#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sweep `.board_identity.json` ONLY when it is a drifted or guest record. Never blindly.

⚠⚠ WHY THIS EXISTS INSTEAD OF `rm -f`. The standing routine said "after any render/CDP session,
`rm -f tv/.board_identity.json` before pushing", because a CDP load can write a GUEST record and
five TestV2072 assertions then fail with a drift reason that names none of it. That is a real
scar and the removal is right FOR THAT RECORD.

MEASURED 2026-09-09, on the record actually sitting there:

    firstSeen           01:04:20
    his console started 01:04:29     <- NINE SECONDS LATER
    lastSeen            01:25:14   seenCount 28   <- still being written, live
    owner=True  pfx=''  previous=None            -> board_identity_drift() == "ok"

That was his console's LIVE world record, not a harness leftover. Removing it would have destroyed
a healthy `ok` and left `unknown` — and `board_identity_drift`'s own docstring says unknown is
deliberate and is NOT ok, "because a world nobody has seen cannot be shown to be the same one".
Worse, the next write starts a fresh id with `previous: None`, which is the exact shape that makes
a real board read as a stranger's world. [[board-claim-pinned-to-a-mutable-id]]

★ SO THE RULE IS THE RECORD'S STATE, NOT THE RITUAL. The three states the writer can produce map
cleanly onto what should happen, and nothing else needs to be remembered:

    previous is set            -> DRIFTED. a different install came back. sweep (backed up first)
    not owner and pfx          -> GUEST. the CDP case the scar is about. sweep (backed up first)
    owner, no pfx, no previous -> OK. HIS WORLD. keep. removing it degrades ok -> unknown
    no file at all             -> UNKNOWN. nothing to do, and say so rather than reporting success

⚠ AND IT REFUSES WHILE HIS CONSOLE IS RUNNING. A live writer owns that file; sweeping under it
races the process and can leave a half-written record that reads as neither state.
[[borrowed-surface]] [[unknown-stays-unknown]]
"""
import io
import json
import os
import shutil
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))

#: Backups go OUTSIDE the repo, because the whole point is that this file is recoverable.
BACKUP_DIR = os.path.expanduser("~/d2r_board_backups")

#: His console. Never ours to race.
CONSOLE_PORT = 17772

OK, GUEST, DRIFTED, ABSENT, UNREADABLE = "OK", "GUEST", "DRIFTED", "ABSENT", "UNREADABLE"


def path_for(root=None):
    return os.path.join(root or HERE, ".board_identity.json")


def classify(rec):
    """-> (state, why). Mirrors control_app.board_identity_drift's own reasoning."""
    if rec is None:
        return ABSENT, "no record on disk — a world nobody has seen is UNKNOWN, not clean"
    if rec.get("previous"):
        return DRIFTED, ("the board came back as a different install: %s (profile %r), was %s"
                         % (rec.get("id"), rec.get("profile"),
                            (rec.get("previous") or {}).get("id")))
    if (not rec.get("owner")) and rec.get("pfx"):
        return GUEST, ("an UNCLAIMED guest world (pfx=%r) — this is the record a CDP probe leaves, "
                       "and the one the sweep exists for" % rec.get("pfx"))
    return OK, "owner=%s pfx=%r previous=None — a healthy claim" % (rec.get("owner"),
                                                                   rec.get("pfx"))


def console_is_running(port=CONSOLE_PORT):
    """-> pid or None. Never kills, never touches it; only asks."""
    try:
        import subprocess
        out = subprocess.run(["lsof", "-ti", "tcp:%d" % int(port)],
                             capture_output=True, text=True, timeout=10).stdout.strip()
        return int(out.split("\n")[0]) if out else None
    except Exception:
        return None


def read(p):
    try:
        with io.open(p, encoding="utf-8") as fh:
            return json.load(fh), None
    except FileNotFoundError:
        return None, None
    except Exception as e:
        return None, type(e).__name__


def sweep(root=None, force=False, dry=False):
    """-> dict. Removes the record ONLY when it is GUEST or DRIFTED."""
    p = path_for(root)
    rec, err = read(p)
    if err:
        return {"action": "kept", "state": UNREADABLE,
                "why": "the record could not be parsed (%s) — refusing to delete what cannot be "
                       "read, because an unreadable file is not a proven-bad one" % err,
                "path": p}
    state, why = classify(rec)
    out = {"state": state, "why": why, "path": p, "action": "none"}
    if state in (ABSENT,):
        out["action"] = "none"
        return out
    if state == OK and not force:
        out["action"] = "kept"
        out["why"] = why + " — KEPT. Removing it turns ok into unknown, which is worse."
        return out
    pid = console_is_running()
    if pid:
        out["action"] = "refused"
        out["why"] = ("his console is running (pid %d) and owns this file — sweeping under a live "
                      "writer can leave a half-written record that reads as neither state" % pid)
        return out
    if dry:
        out["action"] = "would-sweep"
        return out
    try:
        if not os.path.isdir(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)
        dest = os.path.join(BACKUP_DIR, "board_identity_%s_%s.json"
                            % (state.lower(), time.strftime("%Y%m%d_%H%M%S")))
        shutil.copy(p, dest)
        os.remove(p)
        out["action"] = "swept"
        out["backup"] = dest
    except Exception as e:
        out["action"] = "failed"
        out["why"] = "%s: %s" % (type(e).__name__, str(e)[:120])
    return out


def main(argv):
    dry = "--dry" in argv
    force = "--force" in argv
    r = sweep(dry=dry, force=force)
    print("  board identity: %-9s %s" % (r["state"], r["why"]))
    print("  action        : %s%s" % (r["action"],
                                      ("  -> " + r["backup"]) if r.get("backup") else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
