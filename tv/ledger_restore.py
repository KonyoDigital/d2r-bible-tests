# -*- coding: utf-8 -*-
"""v2735 — THE WIRE BETWEEN THE AUTOMATIC BACKUP AND THE DOOR THAT CAN PUT IT BACK.

Konyo: *"i want this automated not relying on the user.. i want a backup and restore point updated
and able to be repaired/restored thats why we coded all this already in parts just needs to be
wired properly."*

He was exactly right about the shape of it. MEASURED:

    BACKUP   automatic every 600s, all five ledgers + route, census-driven   ✅ v2731
    REBUILD  derives a chronicle from the other ledgers                      ✅ v2732
    DOORS    /api/chronicle_apply and /api/vault_apply — live, and the
             console UI already calls both                                   ✅
    RESTORE  ~/d2r_ledger_backups/restore_ledger.py — a manual CLI OUTSIDE
             the repo, dry-run by default, picking a file by HEURISTIC and
             never asking which profile                                      ❌ NOT WIRED

Nothing joined a backup file to those doors. The only "restore" reachable from the console was
`board_restore_dates`, which rewrites DATES on rows that still exist and cannot recover a loss.
[[the-unjoined-end]] [[plumbing-with-no-tap]]

=== WHY THIS IS SAFE TO BUILD NOW AND WAS NOT BEFORE ===
v2731 stamped the ROUTE into every backup file. Before that, a restore could only act on "whatever
board is currently showing" and nothing in the file would contradict a cross-world restore — the
Dean defect in reverse. Picking by route is now possible, so this refuses rather than guesses.

=== AND WHY THE APPLY IS ADDITIVE BY CONSTRUCTION ===
`chronicle_apply` routes through the board's own `window.chronicleApply`, which its own docstring
describes as "dated, merge-max, undoable". MERGE-MAX means a restore can only put back what is
missing; it cannot overwrite a newer find with an older one. So the dangerous direction — an old
snapshot clobbering good data — is closed by the door itself, not by a promise here.

⚠⚠ THIS MODULE WRITES NOTHING AND CANNOT. It reads backups, compares, and returns a PROPOSAL in the
shape the board already accepts (`{wouldAdd: {uniques, sets}}`). The console never writes the
ledger — every existing path asks the board to press its own door, and a second writer into his
chronicle is the drift this repo keeps finding.

⚠ THE RESTORE IS NOT AUTOMATIC, DELIBERATELY. "Able to be restored" is his phrase. The BACKUP is
the automated half and he never touches it; putting a ledger back is a deliberate act, and a plan
that ran itself could resurrect a state he had intentionally left behind.
"""
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
BACKUP_DIR = os.path.expanduser("~/d2r_ledger_backups")

#: The stores a restore can put back through the board's own door, and which half of the
#: proposal each belongs to. ⚠ rwMade and gameFound are BACKED UP (v2731) but are NOT restorable
#: through `chronicleApply` — it accepts uniques and sets. Saying so is the point: a restore that
#: silently covered three of five stores while reporting success would be the worst kind.
RESTORABLE = {"foundLog": "uniques", "setPieces": "sets"}

#: ⚠⚠ THE THREE THAT CANNOT TRAVEL BACK, AND WHY EACH — because the obvious "fix" for one of them
#: would defeat a gate that exists on purpose. Measured 2026-09-06:
#:
#:   owned      `/api/vault_apply` exists and looks like the door for it. It is NOT.
#:              vault_apply RE-GATES any caller-supplied proposal through `_vault_retro()` —
#:              KEEP_MIN_WITNESSES = 3, KEEP_CONF_FLOOR = 0.55 — and a restore has a backup FILE,
#:              not three distinct sessions of testimony. Posting a restore through it would either
#:              be rejected (correct) or, if someone widened the gate to let it through, would put
#:              uncorroborated rows in his stash with nothing behind them. That gate was added in
#:              v1595 precisely because a hand-made body used to go straight through, and a
#:              cross-family pass on v2641 found two more holes in it. Do not reopen them for this.
#:   rwMade     the board exposes no apply door for forged runewords at all
#:   gameFound  in-game records the board writes from the game, not from a tick
#:
#: They are still BACKED UP, which is the half that matters most — the data survives. Getting them
#: back is a door that does not exist yet, and saying so on every plan is the point: a restore that
#: silently covered two of five stores while reporting success is the worst kind.
BACKED_UP_ONLY = ("rwMade", "gameFound", "owned")


def _route_key(route):
    """A route dict -> the key a backup file is matched on. -> str or None."""
    if not isinstance(route, dict):
        return None
    rid = str(route.get("id") or "").strip()
    prof = str(route.get("p") or "").strip()
    if not rid:
        return None
    return "%s|%s" % (rid, prof or "main")


def backups_for(route, d=None):
    """Every backup file whose stamped route matches, newest first. -> (list, why)

    ⚠ MATCHED ON THE ROUTE, NEVER PICKED BY HEURISTIC. `restore_ledger.py` chose "the file with the
    most unique-like names", which is a guess wearing a measurement's clothes and could cross
    worlds. Files written before v2731 carry no route at all and are SKIPPED with a reason — an
    unrouted backup is not this profile's backup, it is a backup whose owner is unknown.
    [[unknown-stays-unknown]]
    """
    want = _route_key(route)
    if not want:
        return [], "no route was given, so no backup can be matched to a profile"
    d = d or BACKUP_DIR
    if not os.path.isdir(d):
        return [], "there is no backup directory at %s" % d
    hits, unrouted = [], 0
    try:
        names = sorted(os.listdir(d), reverse=True)
    except Exception as e:
        return [], "the backup directory could not be read (%s)" % str(e)[:60]
    for n in names:
        if not (n.startswith("ledger_") and n.endswith(".json")):
            continue
        p = os.path.join(d, n)
        try:
            with io.open(p, encoding="utf-8") as fh:
                blob = json.load(fh)
        except Exception:
            continue                       # unreadable file: not a candidate, and not an error here
        got = _route_key((blob or {}).get("route"))
        if got is None:
            unrouted += 1
            continue
        if got == want:
            hits.append((p, blob))
    why = ""
    if not hits:
        why = ("no backup carries this profile's route (%s); %d file(s) predate the route stamp "
               "and cannot be attributed to anyone" % (want, unrouted))
    elif unrouted:
        why = ("%d file(s) predate the route stamp and were skipped — they may be this profile's "
               "and there is no way to tell" % unrouted)
    return hits, why


def plan(route, current, d=None):
    """What the newest matching backup would put back. -> dict. Reads only.

    `current` is the board's ledger as it stands now: {"foundLog": {...}, "setPieces": [...], ...}
    A store the caller could not read must be passed as None, not {} — restoring INTO an unknown
    is how a restore invents a loss.
    """
    hits, why = backups_for(route, d)
    if not hits:
        return {"ok": False, "why": why or "no matching backup"}
    path, blob = hits[0]
    led = (blob or {}).get("ledger") or {}
    out, missing_total = {}, 0
    for store, half in sorted(RESTORABLE.items()):
        have = current.get(store)
        if have is None:
            out[store] = {"half": half, "missing": None,
                          "why": "the board's %s could not be read, so what is missing from it is "
                                 "UNKNOWN — not everything, and not nothing" % store}
            continue
        backed = led.get(store)
        if not isinstance(backed, (dict, list)):
            out[store] = {"half": half, "missing": None,
                          "why": "the backup carries no %s to restore from" % store}
            continue
        have_set = set(have if isinstance(have, list) else have.keys())
        back_keys = list(backed if isinstance(backed, list) else backed.keys())
        gap = [k for k in back_keys if k not in have_set]
        missing_total += len(gap)
        out[store] = {"half": half, "missing": gap, "count": len(gap),
                      "inBackup": len(back_keys), "onBoard": len(have_set),
                      "why": "%d name(s) are in the backup and not on the board" % len(gap)}
    return {
        "ok": True, "file": os.path.basename(path), "takenAt": (blob or {}).get("takenAt"),
        "route": (blob or {}).get("route"), "stores": out, "missingTotal": missing_total,
        # ⚠ SAID, NOT SILENTLY OMITTED. Three backed-up stores cannot travel through this door.
        "notRestorableHere": list(BACKED_UP_ONLY),
        "why": ("%s would put back %d name(s) across %d store(s); %s are backed up but cannot be "
                "restored through the chronicle door and need their own path"
                % (os.path.basename(path), missing_total, len(RESTORABLE),
                   ", ".join(BACKED_UP_ONLY))),
    }


def proposal_from(plan_out):
    """Shape a plan into what the BOARD already accepts. -> dict or None. Writes nothing.

    The board's `window.chronicleApply` reads `proposal.wouldAdd`, so a restore is expressed in the
    same vocabulary a sweep uses. Nothing new is invented at the door.
    """
    if not (isinstance(plan_out, dict) and plan_out.get("ok")):
        return None
    add = {}
    for store, row in (plan_out.get("stores") or {}).items():
        gap = row.get("missing")
        if not gap:
            continue
        half = row.get("half")
        add.setdefault(half, {})
        for name in gap:
            # a restore asserts only that the name BELONGED — the board owns dating it, exactly as
            # it does for a hand tick. Inventing a date here would put a time on his screen that
            # nothing witnessed. [[unknown-stays-unknown]]
            add[half][name] = []
    if not add:
        return None
    return {"wouldAdd": add, "source": "ledger_restore", "file": plan_out.get("file")}
