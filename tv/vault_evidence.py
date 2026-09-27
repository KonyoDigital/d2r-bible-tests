# -*- coding: utf-8 -*-
"""What a vault reset may put back, and only from evidence.

His ruling 2026-09-27: a reset clears the marks. An item comes back when its own looks prove it,
Wilson-style, or when it is the kind of thing that does not vanish by itself (equipped on the main
character, a sunder, Annihilus, Hellfire Torch, Gheed's). One tier table. The bound is
confidence.wilson_lower, not a second copy of that sum.

tier() and rebuild_plan() decide. plan_from_ledger() only reads a ledger the caller names and
turns its rows into that shape. It does not write the ledger and it does not file a mark.
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import confidence as _confidence

# The vault-apply bar already measured in this tree. 10 successes in 10 trials lands on it.
# A perfect 9 trials is 0.701, under that bar, so "under 10" and the bar agree on every
# perfect record. The trial floors still decide hardened, and a record with misses.
WILSON_BAR = 0.722
TRIALS_PROVEN = 10
TRIALS_HARDENED = 20
WATCHED, PROVEN, HARDENED = "WATCHED", "PROVEN", "HARDENED"

# Items that do not disappear because a stash was sorted. They are rebuilt even below the bar.
KEPT_KINDS = frozenset(("sunder", "annihilus", "torch", "gheed"))


def tier(successes, trials):
    """-> {tier, bound, successes, trials, why}. tier is None when the counts cannot be read."""
    try:
        k = int(successes)
        n = int(trials)
    except (TypeError, ValueError):
        return {"tier": None, "bound": None, "successes": None, "trials": None,
                "why": "the look counts could not be read, so the tier is UNKNOWN"}
    if n < 0 or k < 0:
        return {"tier": None, "bound": None, "successes": None, "trials": None,
                "why": "a negative look count is not a measurement"}
    if k > n:
        k = n
    bound = _confidence.wilson_lower(k, n)
    if n < TRIALS_PROVEN or bound < WILSON_BAR:
        name = WATCHED
    elif n >= TRIALS_HARDENED:
        name = HARDENED
    else:
        name = PROVEN
    return {"tier": name, "bound": bound, "successes": k, "trials": n, "why": ""}


def rebuild_plan(items):
    """Which cleared marks come back. `items` is the evidence already in hand, not a file.

    Each item is {name, successes, trials} and may say equipped=True or kind= one of KEPT_KINDS.
    A WATCHED item stays cleared. PROVEN is re-filed. HARDENED is re-filed and locked.
    An equipped item or a kept kind comes back even below the bar, and says why.
    """
    rebuilt, held = [], []
    if not isinstance(items, list):
        return {"ok": False, "rebuilt": [], "held": [],
                "why": "the evidence could not be read, so nothing is rebuilt and nothing is called empty"}
    for it in items:
        if not isinstance(it, dict) or not it.get("name"):
            continue
        got = tier(it.get("successes"), it.get("trials"))
        row = {"name": it["name"], "tier": got["tier"], "bound": got["bound"],
               "successes": got["successes"], "trials": got["trials"]}
        kept = bool(it.get("equipped")) or str(it.get("kind") or "") in KEPT_KINDS
        if got["tier"] is None:
            row["why"] = got["why"]
            held.append(row)
        elif got["tier"] == WATCHED and not kept:
            row["why"] = "below the proven bar"
            held.append(row)
        else:
            row["locked"] = got["tier"] == HARDENED
            row["why"] = ("kept kind" if kept and got["tier"] == WATCHED else got["tier"])
            rebuilt.append(row)
    return {"ok": True, "rebuilt": rebuilt, "held": held, "why": ""}


_UNREAD = ("the witness ledger could not be read, so nothing is rebuilt "
           "and nothing is called empty")
# Where his MAIN carries a thing. The same places the filing door refuses as a mule witness.
_MAIN_LANES = frozenset(("equipment", "equipped", "inventory", "belt", "cube"))


def _unread(why=None):
    return {"ok": False, "rebuilt": [], "held": [], "why": why or _UNREAD}


def _conf_floor():
    """The look floor the vault gate already uses. None when that module cannot be read."""
    try:
        import vault_retro as VR
        return float(VR.KEEP_CONF_FLOOR)
    except Exception:
        return None


def _kind_of(rows):
    for row in rows:
        kind = str(row.get("kind") or "").strip().lower()
        if kind in KEPT_KINDS:
            return kind
    name = str(rows[0].get("name") or "").lower()
    for kind in sorted(KEPT_KINDS):
        if kind in name:
            return kind
    return ""


def _equipped_of(rows):
    for row in rows:
        if row.get("equipped") is True:
            return True
        if str(row.get("lane") or "").strip().lower() in _MAIN_LANES:
            return True
    return False


def _is_success(look, floor):
    """A look that saw this item: its own frame, its own conf at the vault floor, and not a miss."""
    if not isinstance(look, dict):
        return False
    saw = str(look.get("saw") or "").strip().lower()
    if saw in ("empty", "other", "miss") or look.get("hit") is False:
        return False
    frame = str(look.get("frame") or "").strip()
    if not frame:
        return False
    try:
        conf = float(look.get("conf"))
    except (TypeError, ValueError):
        return False
    return conf >= floor


def _group(rows):
    order, buckets = [], {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or "").strip()
        if not name:
            continue
        if name not in buckets:
            buckets[name] = []
            order.append(name)
        buckets[name].append(row)
    return [(name, buckets[name]) for name in order]


def _measure(rows, floor):
    """-> (successes, trials, sessions, cells, witness_sessions) or None when a row cannot be read.

    A missing witness list is UNKNOWN, not zero. An empty list is a real measurement of no looks.
    """
    successes, trials = 0, 0
    sessions, witness_sessions, cells = [], [], []
    seen_sessions, seen_cells = set(), set()
    for row in rows:
        if "witnesses" not in row and "looks" not in row:
            return None
        raw = row.get("witnesses") if "witnesses" in row else row.get("looks")
        if not isinstance(raw, list):
            return None
        if "misses" in row:
            extra = row.get("misses")
            if isinstance(extra, bool) or not isinstance(extra, int) or extra < 0:
                return None
        else:
            extra = 0
        for look in raw:
            trials += 1
            if not isinstance(look, dict):
                continue
            cell = look.get("cell")
            if isinstance(cell, dict) and "x" in cell and "y" in cell:
                key = (str(cell.get("tab") or ""), cell.get("x"), cell.get("y"))
                if key not in seen_cells:
                    seen_cells.add(key)
                    cells.append({"tab": cell.get("tab"), "x": cell.get("x"), "y": cell.get("y")})
            if not _is_success(look, floor):
                continue
            successes += 1
            sid = str(look.get("session") or look.get("witness") or "").strip()
            frame = str(look.get("frame") or "").strip()
            if not sid or not frame or sid in seen_sessions:
                continue
            seen_sessions.add(sid)
            sessions.append(sid)
            try:
                conf = float(look.get("conf"))
            except (TypeError, ValueError):
                continue
            witness_sessions.append({
                "witness": sid, "session": sid, "frame": frame, "conf": conf,
            })
        trials += extra
    return successes, trials, sessions, cells, witness_sessions


def plan_from_ledger(path):
    """Read one witness ledger and ask rebuild_plan. Never writes the file.

    `path` is the caller's file. This does not know where his ledger lives, and a path that
    cannot be read is UNKNOWN — rebuilt stays empty and ok is false, which is not "nothing proven".
    """
    if not path or not os.path.isfile(path):
        return _unread()
    try:
        with io.open(path, "rb") as fh:
            blob = fh.read()
    except Exception:
        return _unread()
    try:
        doc = json.loads(blob.decode("utf-8"))
    except Exception:
        return _unread()
    if not isinstance(doc, dict) or not isinstance(doc.get("owned"), list):
        return _unread()
    floor = _conf_floor()
    if floor is None:
        return _unread()
    items, filing = [], {}
    for name, rows in _group(doc["owned"]):
        measured = _measure(rows, floor)
        if measured is None:
            item = {"name": name, "successes": None, "trials": None}
            extra = {"equipped": _equipped_of(rows), "kind": _kind_of(rows),
                     "cells": [], "sessions": [], "witness": None}
        else:
            successes, trials, sessions, cells, witness_sessions = measured
            item = {"name": name, "successes": successes, "trials": trials,
                    "equipped": _equipped_of(rows), "kind": _kind_of(rows)}
            extra = {"equipped": item["equipped"], "kind": item["kind"],
                     "cells": cells, "sessions": sessions,
                     "witness": {"lane": "stash", "by": "evidence", "sessions": witness_sessions}}
        items.append(item)
        filing[name] = extra
    plan = rebuild_plan(items)
    if not plan.get("ok"):
        return plan
    for row in plan["rebuilt"]:
        extra = filing.get(row["name"]) or {}
        row["equipped"] = bool(extra.get("equipped"))
        row["kind"] = extra.get("kind") or ""
        row["cells"] = extra.get("cells") or []
        row["sessions"] = extra.get("sessions") or []
        witness = extra.get("witness")
        if isinstance(witness, dict):
            witness = dict(witness)
            witness["wilson"] = row.get("bound")
            witness["gate"] = {"pass": True, "why": row.get("why"),
                               "looks": row.get("successes"), "wilson": row.get("bound")}
        row["witness"] = witness
        row["home"] = "__keep" if (row["equipped"] or row["kind"] in KEPT_KINDS) else None
    try:
        with io.open(path, "rb") as fh:
            again = fh.read()
    except Exception:
        return _unread()
    if again != blob:
        return _unread("the witness ledger changed while it was read, so nothing is rebuilt "
                       "and nothing is called empty")
    return plan


def cited_frames(path):
    """Frame files a WATCHED, PROVEN or HARDENED item stands on. Never writes the ledger.

    A missing file is a measurement of nothing cited. A file that will not parse is UNKNOWN:
    `frames` is None, and a deleter that cannot tell must keep every picture.
    Only a look that saw the item is cited. A miss is not.
    """
    if not path or not os.path.isfile(path):
        return {"ok": True, "frames": [], "why": "there is no witness ledger at this path, so no frame is cited"}
    try:
        with io.open(path, "rb") as fh:
            blob = fh.read()
    except Exception:
        return {"ok": False, "frames": None, "why": _UNREAD}
    try:
        doc = json.loads(blob.decode("utf-8"))
    except Exception:
        return {"ok": False, "frames": None, "why": _UNREAD}
    if not isinstance(doc, dict) or not isinstance(doc.get("owned"), list):
        return {"ok": False, "frames": None, "why": _UNREAD}
    floor = _conf_floor()
    if floor is None:
        return {"ok": False, "frames": None, "why": _UNREAD}
    found, seen = [], set()
    for name, rows in _group(doc["owned"]):
        measured = _measure(rows, floor)
        if measured is None:
            continue
        successes, trials, _sessions, _cells, shots = measured
        got = tier(successes, trials)
        if got["tier"] not in (WATCHED, PROVEN, HARDENED):
            continue
        for shot in shots:
            base = os.path.basename(str(shot.get("frame") or ""))
            if not base or base in seen:
                continue
            seen.add(base)
            found.append(base)
    try:
        with io.open(path, "rb") as fh:
            if fh.read() != blob:
                return {"ok": False, "frames": None, "why": _UNREAD}
    except Exception:
        return {"ok": False, "frames": None, "why": _UNREAD}
    return {"ok": True, "frames": found, "why": ""}
