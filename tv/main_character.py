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
# names_loc (g5 / journal) spells this "equipped". The scene classifier never emits either.
# Accepting only one spelling is how a fed learner still pins equip at 0. [[the-unjoined-end]]
EQUIPMENT_ALIASES = (EQUIPMENT_LANE, "equipped")
_LOCK_FLOOR = 0.43          # 3-of-3 clears it; the same floor the vault's KEEP rule uses
_MIN_SIGHTINGS = 3          # "1 frame is a fixture; 2 is a coincidence" — his own witness rule


def lane_from_sighting(activity, names_loc=None):
    """Which lane a sighting should teach. -> str|None

    names_loc "equipped" is the ONLY safe equipment signal: it is a per-name location from the
    reader, not a frame class. Promoting every inventory FRAME to equipment would fire on charms,
    the cube and the tomes and lock them as gear. [[unknown-stays-unknown]]
    """
    loc = str(names_loc or "").strip().lower()
    if loc in EQUIPMENT_ALIASES:
        return EQUIPMENT_LANE
    act = str(activity or "").strip().lower()
    return act or None


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
    if str(lane or "").strip().lower() in EQUIPMENT_ALIASES:
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


def equip_sightings():
    """How many sightings have EVER landed in the equipment lane. -> int

    This is the input the whole lock rule is a function of. Reported separately because a zero
    here and a zero in `locked` mean completely different things, and only one of them improves
    with more farming.
    """
    n = 0
    for row in (_load() or {}).values():
        if isinstance(row, dict):
            n += int(row.get("equip") or 0)
    return n


def blocked_why():
    """Why nothing can lock, or None if nothing is blocking it. -> str | None

    ⚠ THE POINT OF THIS FUNCTION IS THAT `locked: 0` HAS TWO MEANINGS AND ONLY ONE IS BENIGN.
    "No item has cleared the floor YET" invites him to keep farming. "No item can EVER clear the
    floor" is a defect. They print identically, and the second was being reported as OK.

    `equip` increments only for lane == "equipment" (see saw()). That lane comes from
    reel_segments.activity_at, whose whole vocabulary is stash · inventory · gameplay · town ·
    transition — there is no equipment member, so no frame can ever yield it.
    """
    tracked = len(_load() or {})
    if not tracked:
        return None                       # nothing recorded at all is a different, honest empty
    if equip_sightings():
        return None                       # the lane IS being fed; a zero lock is then genuine
    try:
        import reel_segments as _rs
        vocab = tuple(getattr(_rs, "_GRID_ACTIVITIES", ())) + tuple(
            getattr(_rs, "_NO_GRID_ACTIVITIES", ()))
    except Exception:
        vocab = ()
    if vocab and EQUIPMENT_LANE not in vocab:
        return ("no sighting has EVER reached the equipment lane. activity_at cannot return %r "
                "(reel_segments knows only %s). The remaining door is names_loc 'equipped' via "
                "lane_from_sighting — adding an equipment FRAME CLASS would fire on inventory "
                "grids and lock charms as gear. Zero equip sightings means that door has not "
                "been fed, not that a scene is missing." % (EQUIPMENT_LANE, " · ".join(vocab)))
    return ("no sighting has ever reached the equipment lane, so every confidence is 0.0 and "
            "nothing can lock — the ledger is being fed, but never from that lane")


def report():
    _blocked = blocked_why()
    return {"locked": equipped(), "tracked": len(_load() or {}),
            "floor": _LOCK_FLOOR, "minSightings": _MIN_SIGHTINGS,
            "equipSightings": equip_sightings(),
            # None means nothing is structurally in the way; a string is the reason it is.
            "blockedWhy": _blocked,
            "canEverLock": _blocked is None,
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
        if r.get("blockedWhy"):
            print("   \u26a0 NOTHING CAN LOCK, and that is not the same as nothing having earned it:")
            print("     %s" % r["blockedWhy"])
        else:
            print("   nothing has earned a lock yet — that is an honest empty, not a failure")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv))
