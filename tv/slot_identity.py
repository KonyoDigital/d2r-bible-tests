#!/usr/bin/env python3
"""SLOT IDENTITY — WHERE an item was seen, not just THAT it was seen.

Konyo, 2026-08-29: "register the spot it saw the item/tooltip within the inventory or stash..
whats most important to be registered in the vault and be auto assembled it needs to be read within
the tooltip and where and what cell box its located so it can have a slot identity for each item..
and it should be registered and tallied as an additive not a definite.. same as the console wilson
score to prove it and for accuracy to be better."

And on the two lanes:
  "dont forget when we do specific routes to stash/vault it bypasses the witnesses"
  "meaning when i do it and its not shadow"  /  "shadow should have those extra safeguards"
  "but me/cuzin/user doesnt need to be witnessed.. just needs to be able to read it accurately..
   so maybe just a double read... or something to also lock down that so its accurate"
  "not just witnesses — ALL the logic we coded.. same for me... it should simply be accurate with
   safeguard and recheck verification"

⚠ THIS MODULE DECIDES NOTHING AND DELETES NOTHING. It is the same shape as prune_shadow: it
computes, it explains, and it refuses to answer when it cannot. The existing gate in
chronicle_retro (witnesses / wilson_shadow) stays the authority on grounding; this adds the field
that gate never had, and the human-lane bar that gate has no way to express.

WHY IT DOES NOT TOUCH THE LOCKED INTAKE. d2r_intake_LOCKED pins the reader (Sonnet + crop) and must
not change. It does not have to: a cell is DERIVABLE FROM PIXELS. D2R's containers are fixed grids,
so given the panel's box in the frame and a point inside it, the cell is arithmetic. The reader
keeps reading names; this reads geometry.
"""

# D2R container geometry — fixed by the game, in CELLS (cols, rows).
# ⚠ These are the game's numbers, not tuning knobs. A stash TAB is 10x10 in Resurrected;
# the inventory is 10x4; the Horadric Cube is 3x4. If a future patch changes them, they change
# here and every derived slot changes with them, which is why they are named rather than inlined.
GRIDS = {
    "stash":     (10, 10),
    "inventory": (10, 4),
    "cube":      (3, 4),
}


def cell_of(point, panel_box, container):
    """Which cell does this point fall in? -> (col, row) or (None, why)

    `point` is (x, y) in frame pixels. `panel_box` is (left, top, width, height) of the CONTAINER
    GRID in the same frame — not the window, the grid. `container` is a key of GRIDS.

    Returns ((col, row), None) on success or (None, reason) on refusal. It refuses rather than
    guessing, because a slot that is wrong is worse than a slot that is absent: an absent slot
    leaves the item unplaced, a wrong one files it somewhere he will not look.
    """
    if container not in GRIDS:
        return None, "unknown container %r — the grid is not one this game has" % (container,)
    try:
        px, py = float(point[0]), float(point[1])
        bx, by, bw, bh = [float(v) for v in panel_box]
    except (TypeError, ValueError, IndexError):
        return None, "point or panel box is not numeric"
    if bw <= 0 or bh <= 0:
        return None, "panel box measures %gx%g — nothing can be inside it" % (bw, bh)
    cols, rows = GRIDS[container]
    if not (bx <= px < bx + bw and by <= py < by + bh):
        return None, ("the point (%g,%g) is OUTSIDE the %s grid (%g,%g %gx%g) — a tooltip anchored "
                      "outside the panel is not evidence about a cell in it"
                      % (px, py, container, bx, by, bw, bh))
    col = int((px - bx) / (bw / cols))
    row = int((py - by) / (bh / rows))
    col = min(max(col, 0), cols - 1)
    row = min(max(row, 0), rows - 1)
    return (col, row), None


def slot_key(container, col, row, tab=None):
    """A stable, readable identity for one cell. -> str

    `tab` is the stash tab (personal / shared 1..3, or whatever the caller names it); it is part of
    the identity because the same (col,row) in two tabs is two different places.
    """
    where = "%s%s" % (container, ("[%s]" % tab) if tab not in (None, "") else "")
    return "%s:c%dr%d" % (where, int(col), int(row))


def slot_of_sighting(s):
    """The slot a sighting claims, or None. -> str|None

    A sighting may carry `slot` already (a caller that computed it), or the raw material to compute
    one: `point`, `panelBox`, `container`, optional `tab`.
    """
    if not isinstance(s, dict):
        return None
    if s.get("slot"):
        return str(s["slot"])
    pt, box, cont = s.get("point"), s.get("panelBox"), s.get("container")
    if pt and box and cont:
        cell, why = cell_of(pt, box, cont)
        if cell:
            return slot_key(cont, cell[0], cell[1], s.get("tab"))
    return None


def slot_tags(sightings):
    """Witness tags that only a SLOT can earn. -> sorted list

    `same-slot`     two or more sightings agree the item was in the same cell. That is corroboration
                    the name alone cannot give: two reads of one panel can share a misread of the
                    TEXT, but agreeing on the cell as well means they agree about a second,
                    independent fact.
    `slot-conflict` the same item is claimed in two different cells WITHIN ONE REEL. Items do not
                    move mid-reel unless he moved them, so this is a signal to hold, not to ground.
                    It is returned as a tag rather than an exception because the gate decides.
    """
    seen = {}
    for s in (sightings or []):
        k = slot_of_sighting(s)
        if not k:
            continue
        reel = str((s or {}).get("reel") or "")
        seen.setdefault(reel, set()).add(k)
    tags = set()
    allslots = set()
    for reel, ks in seen.items():
        allslots |= ks
        if len(ks) >= 2:
            tags.add("slot-conflict")
    placed = sum(1 for s in (sightings or []) if slot_of_sighting(s))
    if placed >= 2 and len(allslots) == 1:
        tags.add("same-slot")
    return sorted(tags)


def placement(sightings):
    """How much of the evidence carries a place at all. -> dict

    ⚠ UNPLACED IS NOT ZERO. A sighting with no slot has not been shown to be anywhere; it has not
    been shown to be nowhere either. The two are reported separately so a caller can never read
    "no slot conflicts" as "every read agreed on a cell". [[unknown-stays-unknown]]
    """
    n = len(sightings or [])
    keys = [slot_of_sighting(s) for s in (sightings or [])]
    placed = [k for k in keys if k]
    distinct = sorted(set(placed))
    return {
        "n": n,
        "placed": len(placed),
        "unplaced": n - len(placed),
        "slots": distinct,
        "agreed": (len(distinct) == 1 and len(placed) >= 2),
        "why": ("%d of %d looks carried a cell; %s"
                % (len(placed), n,
                   ("they agree on %s" % distinct[0]) if len(distinct) == 1 and placed
                   else ("they disagree: %s" % ", ".join(distinct)) if len(distinct) > 1
                   else "none of them placed it")),
    }


# ══ THE TWO LANES ═══════════════════════════════════════════════════════════════════════════════
# His rule, exactly: both lanes must be ACCURATE. They differ only in which instrument earns it.
#   SHADOW  — nobody was there, so independence has to be manufactured: witnesses, watchdog, eagle
#             eye, Wilson, confluence. That apparatus already exists in chronicle_retro and stays
#             the authority; slot tags feed INTO it as one more witness.
#   HIS     — he was there. A human driving a specific route to stash or vault is not an unverified
#             claim, so a witness COUNT is the wrong instrument. Everything else still applies, and
#             a RECHECK replaces the witnesses: two reads of the same frame that must agree.
LANE_SHADOW = "shadow"
LANE_HUMAN = "human"


def double_read_agrees(a, b):
    """Do two reads of the SAME frame agree well enough to write? -> (bool, why)

    This is the human lane's whole bar, so it is deliberately strict about what "agree" means:
    the same name AND the same slot, when both carry one. A disagreement HOLDS the item — it never
    picks a side, because there is nothing here that could tell which read was right.
    """
    if not isinstance(a, dict) or not isinstance(b, dict):
        return False, "a double read needs two reads; got %r and %r" % (type(a).__name__, type(b).__name__)
    fa, fb = (a.get("frame") or ""), (b.get("frame") or "")
    if not fa or not fb:
        return False, "a read with no frame cannot be rechecked — there is nothing to read twice"
    if fa != fb:
        return False, ("these are reads of DIFFERENT frames (%s vs %s); that is corroboration, not "
                       "a recheck, and the human lane's bar is the recheck" % (fa, fb))
    na, nb = (a.get("name") or "").strip(), (b.get("name") or "").strip()
    if not na or not nb:
        return False, "a read with no name cannot agree about one"
    if na != nb:
        return False, "the two reads disagree on the NAME: %r vs %r — holding" % (na, nb)
    sa, sb = slot_of_sighting(a), slot_of_sighting(b)
    if sa and sb and sa != sb:
        return False, "the two reads agree on the name but disagree on the CELL: %s vs %s — holding" % (sa, sb)
    where = (" in %s" % sa) if sa else " (no cell on either read)"
    return True, "two reads of %s agree on %r%s" % (fa, na, where)


def lane_verdict(sightings, lane, reads_of_same_frame=None):
    """What this lane requires, and whether it is met. -> dict

    DECIDES NOTHING ON ITS OWN — it reports, and the caller gates. `wouldPass` is a reading, in the
    same spirit as prune_shadow's, so arming any of this is something he can watch rather than a
    switch someone has to trust.
    """
    place = placement(sightings)
    tags = slot_tags(sightings)
    out = {"lane": lane, "placement": place, "slotTags": tags}
    if "slot-conflict" in tags:
        out["wouldPass"] = False
        out["why"] = ("the same item is claimed in two different cells within one reel (%s) — items "
                      "do not move mid-reel unless he moved them, so this holds"
                      % ", ".join(place["slots"]))
        return out
    if lane == LANE_HUMAN:
        pair = list(reads_of_same_frame or [])
        if len(pair) < 2:
            out["wouldPass"] = False
            out["why"] = ("the human lane's bar is a RECHECK, and only %d read of the frame was "
                          "supplied — a single read is not a double read" % len(pair))
            return out
        ok, why = double_read_agrees(pair[0], pair[1])
        out["wouldPass"] = bool(ok)
        out["why"] = why
        return out
    # SHADOW — this module does not re-implement the gate; it hands the gate a richer witness list.
    out["wouldPass"] = None
    out["why"] = ("shadow is gated by chronicle_retro's witnesses + wilson_shadow, which stay the "
                  "authority; slot tags %s are offered to it as additional witnesses"
                  % (tags or "(none)"))
    return out


def say(row):
    """One line a person can read. -> str"""
    v = row.get("wouldPass")
    mark = "✓" if v is True else ("✗" if v is False else "·")
    return "%s [%s] %s" % (mark, row.get("lane"), row.get("why"))


if __name__ == "__main__":
    # REG-044 — this file prints non-ASCII; a non-UTF-8 console would turn its own
    # verdict into a traceback, which is the one place a gate must never be silent.
    import os as _os, sys as _sys
    _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
    try:
        import console_safe as _cs; _cs.enable()
    except Exception:
        pass
    import json, sys
    print(json.dumps({"grids": GRIDS}, indent=1))
    sys.exit(0)
