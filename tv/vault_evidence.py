# -*- coding: utf-8 -*-
"""What a vault reset may put back, and only from evidence.

His ruling 2026-09-27: a reset clears the marks. An item comes back when its own looks prove it,
Wilson-style, or when it is the kind of thing that does not vanish by itself (equipped on the main
character, a sunder, Annihilus, Hellfire Torch, Gheed's). One tier table. The bound is
confidence.wilson_lower, not a second copy of that sum.

This module decides. It does not read his ledger and it does not write a mark.
"""
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
