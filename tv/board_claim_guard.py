#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""REMOVE A GUEST BOARD RECORD. NEVER HIS CLAIM. -> exit 0 always; the VERDICT is on stdout.

⚠⚠ WHY THIS IS CODE AND NOT A SENTENCE. The standing rule read, in full: *"AFTER ANY RENDER/CDP
SESSION: `rm -f tv/.board_identity.json` before pushing — a CDP load writes a GUEST record and five
TestV2072 tests then fail with a drift reason that names none of it."* Every word of that is TRUE
and it is missing its condition, so following it exactly is how you destroy the thing it protects.

MEASURED 2026-09-11. I followed it after a clean render and deleted a record reading `owner: True`
— HIS CLAIM, id `e07a5fe180a8…`, seenCount 1458. The file is gitignored, so `git checkout` could
not bring it back. It survived on two accidents: a backup in `~/d2r_board_backups/` that happened to
carry the same id, and my having PRINTED the id before removing it. The backup was **stale by 677
sightings** (781 vs 1458). Lose that claim for real and his board renders as an empty stranger's
world — 0 of 403, with a claim button that imports nothing. [[board-claim-pinned-to-a-mutable-id]]

A rule with a condition nobody encoded is a rule that depends on the reader being careful at 2am.
This asks OWNER FIRST, and refuses on anything it cannot read.

    owner is True   -> ok      HIS CLAIM. Nothing is removed, ever. Exit 0.
    owner is False  -> drift   a guest/CDP record. Backed up WITH A FRESH SNAPSHOT, then removed.
    anything else   -> unknown unreadable, malformed, or absent. Nothing is removed.

⚠ THE BACKUP IS TAKEN AT REMOVAL TIME, not trusted from the past. The one that saved me was 677
sightings old; a snapshot that is only sometimes current is a safety net with a hole in it.
[[unknown-stays-unknown]] [[stale-reading]]
"""
import io
import json
import os
import shutil
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REC = os.path.join(HERE, ".board_identity.json")
BACKUPS = os.path.expanduser("~/d2r_board_backups")


def read(path=None):
    """-> (state, record|None, why). States match board_identity_drift(): ok | drift | unknown."""
    p = path or REC
    if not os.path.exists(p):
        return "unknown", None, ("no board record on disk — there is nothing to remove, and "
                                 "absent is not the same as a guest record")
    try:
        with io.open(p, encoding="utf-8") as fh:
            d = json.load(fh)
    except Exception as exc:
        return "unknown", None, ("the board record would not parse (%s) — refusing to touch a file "
                                 "whose contents I cannot read" % type(exc).__name__)
    if not isinstance(d, dict):
        return "unknown", None, "the board record is not an object — refusing to touch it"
    own = d.get("owner")
    if own is True:
        return "ok", d, ("this is HIS CLAIM (owner=true, id %s) — it is never mine to remove, and "
                         "deleting it renders his real board as an empty stranger's world"
                         % str(d.get("id"))[:12])
    if own is False:
        return "drift", d, ("a GUEST record (owner=false, pfx %r) — this is the CDP-minted state "
                            "the rule exists for" % (d.get("pfx") or ""))
    return "unknown", d, ("the record carries owner=%r, which is neither true nor false — UNKNOWN, "
                          "and UNKNOWN is not permission" % (own,))


def sweep(path=None, backups=None, act=True):
    """Remove ONLY a guest record, backing it up first. -> dict"""
    p = path or REC
    state, rec, why = read(p)
    out = {"state": state, "why": why, "removed": False, "backup": None}
    if state != "drift" or not act:
        return out
    bdir = backups or BACKUPS
    try:
        if not os.path.isdir(bdir):
            os.makedirs(bdir)
        stamp = time.strftime("%Y%m%d_%H%M%S")
        dest = os.path.join(bdir, "board_identity_guest_%s.json" % stamp)
        shutil.copy2(p, dest)
        out["backup"] = dest
    except Exception as exc:
        out["why"] = ("could not take a fresh backup (%s) — refusing to remove a record I cannot "
                      "first copy" % type(exc).__name__)
        return out
    os.remove(p)
    out["removed"] = True
    return out


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    check_only = "--check" in argv
    r = sweep(act=not check_only)
    icon = {"ok": "\U0001f512", "drift": "\U0001f9f9", "unknown": "❓"}.get(r["state"], "?")
    print("%s board claim: %s" % (icon, r["state"].upper()))
    print("   %s" % r["why"])
    if r["removed"]:
        print("   removed the guest record; fresh backup at %s" % r["backup"])
    elif r["state"] == "drift" and check_only:
        print("   (--check: nothing removed)")
    return 0


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    sys.exit(main())
