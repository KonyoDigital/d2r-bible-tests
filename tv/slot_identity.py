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


# ══ v2332 — WHERE THE GRID ACTUALLY IS, MEASURED ═══════════════════════════════════════════════
# Every entry point in this module takes a `panel_box`, and until now NOTHING IN THE TREE PRODUCED
# ONE. That — not the tooltip offset — is what kept MINI(AUTOMATIC) blocked: point_of_cell answers
# "what must be hovered" and cannot answer it without knowing where the grid is.
#
# THREE INFERENCE ROUTES WERE TRIED AND EACH FAILED, MEASURED RATHER THAN ABANDONED:
#   1. stash_eye.crops_for_aspect() — the OCR crop band. Overlaid on a real frame it drifts off
#      the game's gridlines, and its vertical extent stops ABOVE the grid's bottom edge. It was
#      measured for reading a tab strip, not for cell arithmetic.
#   2. the v2239 `dark_col_idx` lattice — recorded in a ~96-unit downscale of a 937px crop, so one
#      unit is a tenth of a cell. Fitting a 10-column grid to its 6 clusters left residuals of
#      HALF A CELL, and a free pitch with missing lines will always find some fit.
#   3. a full-resolution column-luminance profile — dominated by the ITEMS. Autocorrelation peaks
#      at 159px, not the ~87px cell: a packed stash is darker where the gear is than where the
#      gridlines are.
#
# SO IT IS MEASURED, the same way _TALLY_CROPS was: read off a real frame with a pixel ruler, then
# refined by searching the origin and pitch that put the predicted lines on the darkest pixels.
# Both axes were optimised INDEPENDENTLY and converged on 86.8 and 86.9 px — square, which is what
# a D2R cell is, and a sanity check neither axis was given.
#
#     f_1788104628821.jpg (2940x1912)  ->  x 281  y 381  w 868  h 869   cell 86.8 x 86.9
#
# Verified on the pixels on TWO frames from DIFFERENT sessions, including one with a tooltip over
# the panel: the predicted lines sit on the game's own gridlines across the whole grid.
#
# ⚠ ONLY THE STASH IS CALIBRATED. The inventory is a different panel on the other side of the
# screen and the cube is a third; neither has been measured, so both are REFUSED rather than
# guessed from this one. A wrong cell is worse than no cell — this module says so everywhere else
# and it would be a poor place to start guessing. [[unknown-stays-unknown]]
_PANEL_CAL_FRAME = (2940, 1912)
_PANEL_CAL_ASPECT = _PANEL_CAL_FRAME[0] / float(_PANEL_CAL_FRAME[1])
_PANEL_CAL_LO, _PANEL_CAL_HI = 1.45, 1.62      # the band stash_eye's own crops are locked at

# fractions of the calibration frame, so the numbers survive a resize
PANELS = {
    "stash": (281 / 2940.0, 381 / 1912.0, 868 / 2940.0, 869 / 1912.0),
}


def panel_box_for(frame_w, frame_h, container="stash"):
    """The CONTAINER GRID's box in this frame's pixels. -> ((x, y, w, h), None) or (None, why)

    Refuses rather than guessing on three counts, because each one would place items in real
    cells that are simply the wrong ones:
      · a container nobody has measured
      · a frame whose aspect is outside the calibrated band (D2R anchors the panel to the left and
        scales with HEIGHT, so a different aspect moves the horizontal fractions — the same law
        stash_eye.crops_for_aspect derives, and the same band it trusts)
      · a frame size that is not a frame
    """
    if container not in PANELS:
        return None, ("no panel box has been measured for %r — only %s. Guessing one from the "
                      "stash would put items in real cells that are the wrong ones."
                      % (container, ", ".join(sorted(PANELS))))
    try:
        fw, fh = float(frame_w), float(frame_h)
    except (TypeError, ValueError):
        return None, "frame size is not numeric"
    if fw <= 0 or fh <= 0:
        return None, "frame measures %gx%g — nothing can be inside it" % (fw, fh)
    aspect = fw / fh
    if not (_PANEL_CAL_LO <= aspect <= _PANEL_CAL_HI):
        return None, ("this frame is %.3f aspect and the panel box was measured at %.3f; outside "
                      "%.2f-%.2f the horizontal fractions move and nothing here has been measured "
                      "there yet" % (aspect, _PANEL_CAL_ASPECT, _PANEL_CAL_LO, _PANEL_CAL_HI))
    fx, fy, fwf, fhf = PANELS[container]
    return (fx * fw, fy * fh, fwf * fw, fhf * fh), None


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


def point_of_cell(col, row, panel_box, container, where="center"):
    """The frame point to put the CURSOR on to hover this cell. -> ((x, y), None) or (None, why)

    ★ THE EXACT INVERSE OF cell_of(), and it exists so MINI(AUTOMATIC) can drive the hover itself
    instead of Konyo moving a mouse to twenty cells by hand. cell_of answers "what did he hover";
    this answers "what must be hovered". They MUST agree, or the automatic pass would hover one
    cell and file the result under another — a wrong slot is worse than an absent one, which is the
    rule cell_of already states. The round trip is guarded: point_of_cell -> cell_of returns the
    cell you asked for, for every cell of every grid.

    `where` picks the point inside the cell:
      "center"  — the middle. What a person does, and the safest target.
      "topleft" — a fifth in from the corner, for the calibration pass, because the tooltip anchor
                  is measured RELATIVE to a known corner and the centre hides which corner it was.

    ⚠ IT RETURNS A POINT IN FRAME PIXELS, NOT SCREEN PIXELS, AND THAT IS NOT THE SAME THING.
    Turning one into the other needs the window origin and the capture scale, and neither belongs
    here — this module is pure and has no idea where the game window sits. The caller that moves a
    real cursor must do that conversion and is where the risk lives. [[borrowed-surface]]
    """
    if container not in GRIDS:
        return None, "unknown container %r — the grid is not one this game has" % (container,)
    try:
        c, r = int(col), int(row)
        bx, by, bw, bh = [float(v) for v in panel_box]
    except (TypeError, ValueError, IndexError):
        return None, "cell or panel box is not numeric"
    if bw <= 0 or bh <= 0:
        return None, "panel box measures %gx%g — nothing can be inside it" % (bw, bh)
    cols, rows = GRIDS[container]
    if not (0 <= c < cols and 0 <= r < rows):
        return None, ("cell (%d,%d) is outside the %s grid, which is %dx%d — refusing rather than "
                      "clamping, because a clamped cell would hover a real cell that is not the "
                      "one asked for" % (c, r, container, cols, rows))
    cw, ch = bw / cols, bh / rows
    if where == "topleft":
        return (bx + c * cw + cw / 5.0, by + r * ch + ch / 5.0), None
    return (bx + (c + 0.5) * cw, by + (r + 0.5) * ch), None


def hover_plan(occupied, panel_box, container, where="center"):
    """Cells to hover, in reading order, with the point for each. -> (list, why)

    `occupied` is an iterable of (col, row) the grid reader believes hold an item. Reading order —
    left to right, top to bottom — because that is the order he would do it in, and an order that
    matches his makes a half-finished pass legible instead of scattered.

    Every refusal is CARRIED, not dropped: a cell that cannot be turned into a point appears in the
    plan with point=None and its reason, so a short plan can never be mistaken for a short stash.
    [[unknown-stays-unknown]]
    """
    out, seen = [], set()
    for cell in (occupied or []):
        try:
            c, r = int(cell[0]), int(cell[1])
        except (TypeError, ValueError, IndexError):
            continue
        if (c, r) in seen:
            continue
        seen.add((c, r))
        pt, why = point_of_cell(c, r, panel_box, container, where=where)
        out.append({"col": c, "row": r, "point": pt, "why": why})
    out.sort(key=lambda d: (d["row"], d["col"]))
    ok = [d for d in out if d["point"]]
    return out, (None if ok else "no cell in the plan could be turned into a point")


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


def anchor_from_tooltip_rect(rect, cursor_corner="topleft", offset=(0, 0)):
    """The point the tooltip is ABOUT, from the rectangle the tooltip occupies. -> (point|None, why)

    ⚠ A TOOLTIP IS NOT WHERE THE ITEM IS. D2R draws the tip ADJACENT to the hovered cell, so the
    rectangle tells you where the TEXT went, and the cell is at a fixed offset from one of its
    corners. That offset is a property of the game's layout at a given resolution, and it is the one
    thing here that cannot be derived from a single pair of frames — it has to be measured once
    against a real frame whose true cell is known.

    So this takes the offset as an ARGUMENT and REFUSES when it has not been supplied, rather than
    shipping a plausible constant. A guessed offset would place items in the wrong cell with total
    confidence, which is the failure this whole module is built to avoid.

    tv/tooltip_crop.changed_rect(a, b) already produces `rect` for free on a hover pass — the panel
    is identical frame to frame and only the tip changes, so the rectangle IS the difference. That
    half of the chain exists and is guarded (test_vault_retro's TestV2239). This is the join.

    `rect` is (left, top, right, bottom), matching changed_rect's contract.
    """
    try:
        l, t, r, b = [float(v) for v in rect]
    except (TypeError, ValueError, IndexError):
        return None, "rect is not (left, top, right, bottom)"
    if r <= l or b <= t:
        return None, "rect %r has no area — a tooltip that occupies nothing is not evidence" % (rect,)
    corners = {"topleft": (l, t), "topright": (r, t), "bottomleft": (l, b), "bottomright": (r, b)}
    if cursor_corner not in corners:
        return None, ("unknown corner %r — say which corner of the tip sits by the cell"
                      % (cursor_corner,))
    try:
        ox, oy = float(offset[0]), float(offset[1])
    except (TypeError, ValueError, IndexError):
        return None, "offset is not an (x, y) pair"
    if ox == 0 and oy == 0:
        return None, ("no tooltip->cell OFFSET has been calibrated, so the anchor would be the tip's "
                      "own corner and every item would land in whichever cell the TEXT covers. "
                      "Measure it once against a frame whose true cell is known — that is exactly "
                      "what his 20-item vault test produces — and pass it here. "
                      "[[unknown-stays-unknown]]")
    cx, cy = corners[cursor_corner]
    return (cx + ox, cy + oy), None


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
