#!/usr/bin/env python3
"""WHAT IS ON HIS CHARACTER, LEARNED FROM REPEATED SIGHTINGS AND LOCKED ACCORDINGLY.

★ Konyo: "the locked inventory items that connect and sync to the console vault it should be smart
enough to understand we are always on the MAIN CHARACTER farming so those items that are registered
like horadric cube and tombs and anything EQUIPMENT related (the right side which is inventory when
opened within the template) so it should lock those items accordingly", and then: "it should
register the MAIN CHARACTER and its equipment and start locking in and pinpointing using wilson
score obviously and all techniques related for it".

WHAT ALREADY EXISTED, so that this adds rather than duplicates:
    vault_retro.LOCKED_LANES = ("equipment", "inventory")   the LANE rule — nothing in those two
                                                            lanes is ever told to move. Guarded by
                                                            console_doctor "locked lanes".
    inventory_law.is_locked(name)                           the ITEM rule — the Horadric Cube and
                                                            the tomes are furniture wherever they
                                                            sit.
    confidence.wilson_lower(k, n)                           the same statistic four other lanes use.

WHAT WAS MISSING: neither rule knows WHICH ITEMS ARE HIS GEAR. The lane rule protects anything
currently in the equipment panel, but the moment a reel does not show that panel, the same
Harlequin Crest is just a name with no protection. So a sword he is WEARING could be proposed for
a mule from a frame that only saw the stash.

THE LEDGER, AND WHY IT IS WILSON AND NOT A FLAG. One sighting in the equipment lane is not proof —
a frame can be misread, a lane can be misclassified, and a wrong LOCK is as bad as a wrong move
because it silently removes an item from everything the vault is for. So an item earns its lock:

    k = sightings of this item in the equipment lane
    n = sightings of this item anywhere
    lock when wilson_lower(k, n) >= _LOCK_FLOOR

At 3/3 the floor is 0.438 and at 10/10 it is 0.722, so a thing seen on his character ten times
locks and a thing glimpsed there once does not. That is the same shape as the KEEP witness rule he
already trusts, and it SHARPENS as he plays rather than needing a decision up front.

⚠ IT NEVER UNLOCKS FURNITURE. inventory_law wins outright: the Horadric Cube is locked at zero
sightings, because it is locked by LAW rather than by evidence.
⚠ AND IT DECIDES NOTHING ON ITS OWN. It answers "is this his gear"; whether that blocks a mule is
the vault's call, made where the other refusals live.
"""
import io
import json
import os
import time

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "main_character.json")

EQUIPMENT_LANE = "equipment"
_LOCK_FLOOR = 0.43          # 3-of-3 clears it; the same floor the vault's KEEP rule uses
_MIN_SIGHTINGS = 3          # "1 frame is a fixture; 2 is a coincidence" — his own witness rule


def _load():
    try:
        with io.open(LEDGER, encoding="utf-8") as fh:
            d = json.load(fh)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _save(d):
    try:
        tmp = LEDGER + ".tmp"
        with io.open(tmp, "w", encoding="utf-8") as fh:
            json.dump(d, fh, indent=1, sort_keys=True)
        os.replace(tmp, LEDGER)
    except Exception:
        pass


def _key(name):
    try:
        import retro_gate as _rg
        return _rg.normalise(name)
    except Exception:
        return " ".join(str(name or "").strip().lower().split())


def saw(name, lane, session=None):
    """Record one sighting of `name` in `lane`. -> dict|None

    ⚠ A SESSION COUNTS ONCE PER LANE. Twenty frames of one hover are ONE look at his character, and
    counting them as twenty would let a single pass lock an item outright — the same double-count
    the vault's witness fold exists to stop.
    """
    k = _key(name)
    if not k:
        return None
    d = _load()
    row = d.get(k) or {"name": str(name), "equip": 0, "seen": 0, "sessions": []}
    sid = str(session or "")
    if sid and sid in (row.get("sessions") or []):
        return row                                   # already counted this session
    if sid:
        row.setdefault("sessions", []).append(sid)
        row["sessions"] = row["sessions"][-40:]
    row["seen"] = int(row.get("seen") or 0) + 1
    if str(lane or "").strip().lower() == EQUIPMENT_LANE:
        row["equip"] = int(row.get("equip") or 0) + 1
    row["lastAt"] = int(time.time() * 1000)
    d[k] = row
    _save(d)
    return row


def confidence(name):
    """How sure are we this is on his character? -> (wilson|None, why)"""
    try:
        from confidence import wilson_lower
    except Exception:
        try:
            from tv.confidence import wilson_lower
        except Exception:
            return None, "confidence.wilson_lower is unavailable"
    row = (_load() or {}).get(_key(name))
    if not row:
        return None, "never seen — nothing is known about where this sits"
    k, n = int(row.get("equip") or 0), int(row.get("seen") or 0)
    if n <= 0:
        return None, "no sightings recorded"
    try:
        w = round(float(wilson_lower(k, n)), 3)
    except Exception:
        return None, "the score could not be computed"
    return w, "seen on his character %d of %d times" % (k, n)


def is_locked(name):
    """Should the vault refuse to move this? -> (bool, why)

    Two independent reasons, and the LAW is checked first because it needs no evidence at all.
    """
    try:
        import inventory_law as _il
        if _il.is_locked(name):
            return True, "inventory furniture — locked by law, not by evidence"
    except Exception:
        pass
    row = (_load() or {}).get(_key(name)) or {}
    n = int(row.get("seen") or 0)
    if n < _MIN_SIGHTINGS:
        return False, ("only %d sighting(s) — below the %d-look floor, so nothing is claimed either "
                       "way" % (n, _MIN_SIGHTINGS))
    w, why = confidence(name)
    if w is None:
        return False, why
    if w >= _LOCK_FLOOR:
        return True, "his gear — %s, Wilson floor %.3f" % (why, w)
    return False, "%s, Wilson floor %.3f is below %.2f" % (why, w, _LOCK_FLOOR)


def equipped():
    """Everything currently locked as his gear. -> [ {name, equip, seen, wilson}, ... ]"""
    out = []
    for k, row in sorted((_load() or {}).items()):
        if not isinstance(row, dict):
            continue
        locked, why = is_locked(row.get("name") or k)
        if not locked:
            continue
        w, _ = confidence(row.get("name") or k)
        out.append({"name": row.get("name") or k, "equip": row.get("equip"),
                    "seen": row.get("seen"), "wilson": w, "why": why})
    return out


def report():
    return {"locked": equipped(), "tracked": len(_load() or {}),
            "floor": _LOCK_FLOOR, "minSightings": _MIN_SIGHTINGS,
            "why": ("an item locks when it has been seen at least %d times and its Wilson floor on "
                    "'seen in the equipment lane' clears %.2f" % (_MIN_SIGHTINGS, _LOCK_FLOOR))}


def main(argv=None):
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    r = report()
    print("── HIS MAIN CHARACTER ──")
    print("  %s" % r["why"])
    print("  tracked items: %d · locked: %d" % (r["tracked"], len(r["locked"])))
    for row in r["locked"]:
        print("   %-30s %s" % (row["name"][:30], row["why"]))
    if not r["locked"]:
        print("   nothing has earned a lock yet — that is an honest empty, not a failure")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv))
