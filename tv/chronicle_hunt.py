"""v1789 — THE FOCUSED HUNT: go back and look again, at pixels that can actually add a witness.

Konyo: "cant like an extra AI take care of it and cross reference it with specific and focused hunts
for it to cross reference it here and automatically grail it.. and if it still cant then leave it for
me to tick off."

WHY RE-READING THE SAME FRAME IS NOT CORROBORATION. Same frame, same model, same prompt — a misread
agrees with itself and arrives at the gate wearing a "two witnesses" label. That is the one failure
that could write a fake find into his grail, and it is why `cross-lane` demands a DIFFERENT model
family.

WHY THE FIRST CUT OF THIS FILE COULD NOT HAVE WORKED, measured before it ever shipped. It hunted the
frames NEIGHBOURING a known sighting. Then the arithmetic was actually checked against the six names
his gate was holding:

    Latent Cold Rupture          2 sightings, 1 reel, tags ['cross-frame']
    Latent Crack of the Heavens  3 sightings, 1 reel, tags ['cross-frame']
    Latent Rotting Fissure       3 sightings, 1 reel, tags ['cross-frame']
    Thundergod's Vigor           2 sightings, 1 reel, tags ['cross-frame']
    Toothrow                     4 sightings, 1 reel, tags ['cross-frame']
    Witherstring                 3 sightings, 1 reel, tags ['cross-frame']

Every one of them ALREADY had cross-frame — one on four sightings. `witnesses()` returns a SET, so a
seventh frame in the same reel adds a tag that is already there and the name stays held forever. The
hunt was not under-powered; it was aimed at pixels that could not change the answer. A hunt whose
best possible outcome is the current outcome is a way to spend his subscription on nothing.

WHERE IT AIMS NOW: OTHER REELS. The Chronicle is sorted alphabetically, so a held name's row lies
BETWEEN its alphabetical neighbours in every reel that scrolled past it. Those neighbours are already
in the ledger with their frames, which turns "somewhere in another 400-frame reel" into a bracket of
a few frames. A hit there is `cross-reel` — a genuinely independent observation, on different pixels,
from a different session — and that is the tag these six actually need.

GROK IS ADDITIVE, NEVER REQUIRED. This earns cross-reel from his own footage with Claude alone; when
the Grok lane is on it contributes cross-lane ON TOP. The second eye makes borderline names ground
sooner, so its absence costs coverage, never correctness.

NOTHING IS INVENTED. A name that does not come back stays held, and the remainder is the honest list
he ticks by hand.
"""
import os

import chronicle_retro as cr

PAD = 2                 # frames either side of the bracket — the row may straddle the anchor's page
MAX_PER_NAME = 18       # a bounded hunt; beyond this a name is genuinely single-session
MAX_PER_REEL = 6        # spread the budget across reels, because reels are what earn the tag


def _sort_key(name):
    """The Chronicle's own ordering: alphabetical, case- and punctuation-insensitive."""
    return "".join(ch for ch in str(name or "").replace("’", "'").lower() if ch.isalnum())


def _frame_order(reel_dir):
    """frame name -> position, from the reel's index. Position is what makes 'between' mean anything."""
    idx = cr.load_index(reel_dir) or {}
    order = {}
    for i, f in enumerate(idx.get("frames") or []):
        if f.get("f"):
            order[f["f"]] = i
    return order


def _reel_path(hist_dir, reel):
    r = str(reel or "")
    if not r:
        return None
    p = os.path.join(hist_dir, r if r.startswith("reel_") else "reel_" + r)
    return p if os.path.isdir(p) else None


def _sightings_by_reel(evidence, ledger="uniques"):
    """{reel: {name: [frames]}} over everything ever read."""
    out = {}
    for name, sightings in ((evidence or {}).get(ledger) or {}).items():
        for s in sightings or []:
            reel, frame = s.get("reel"), s.get("frame")
            if reel and frame:
                out.setdefault(reel, {}).setdefault(name, []).append(frame)
    return out


def targets_for(name, evidence, hist_dir, ledger="uniques"):
    """Frames worth reading for `name`, newest reel first, capped.

    Only reels where the name has NO sighting are considered: a hit in a reel it was already seen in
    adds cross-frame, which every held name already has.

    THE UNIT IS THE FRAME, NOT THE REEL, and that was the second correction this function needed.
    The first version bracketed between the target's alphabetical neighbours using their POSITION IN
    THE REEL, which assumes the whole reel is one monotonic scroll. One of his reels is not: 63 names
    across 39 frames, with "War Traveler" at position 2 and "Pelta Lunata" at position 8, because he
    scrolled back up partway through. Bracketing between those two positions aimed the hunt for
    Thundergod's Vigor at the W section — Winged Harpoon, Wire Fleece, Witchwild String — and every
    read there was a guaranteed miss delivered as a clean negative.

    A frame, however, is ALWAYS a contiguous alphabetical page: it is one screenshot of a sorted
    list. So each frame is scored by the alphabetical distance from `name` to the names recorded ON
    that frame, and the closest frames win — plus their immediate neighbours, since the row may sit
    just off the edge of the page. No assumption about the reel's global order survives, which is
    what makes this work on the jumpy reel and the clean ones alike.

    That matters for more than tidiness: the excluded reel is one where a held name is visibly
    present. Refusing to look there was correct given a broken bracket, and wasteful given a working
    one.
    """
    key = _sort_key(name)
    by_reel = _sightings_by_reel(evidence, ledger)
    seen_in = {r for r, names in by_reel.items() if name in names}
    out = []
    for reel in sorted(by_reel, reverse=True):
        if reel in seen_in:
            continue
        path = _reel_path(hist_dir, reel)
        if not path:
            continue
        order = _frame_order(path)
        if not order:
            continue
        # what each frame is known to show, as sort keys
        on_frame = {}
        for other, frames in by_reel[reel].items():
            k = _sort_key(other)
            for f in frames:
                if f in order:
                    on_frame.setdefault(f, []).append(k)
        if not on_frame:
            continue

        def distance(frame):
            """0 when the page BRACKETS the name — the row is on it or within a line of it."""
            ks = on_frame[frame]
            lo, hi = min(ks), max(ks)
            if lo <= key <= hi:
                return 0.0
            near = min(ks, key=lambda k: _key_gap(k, key))
            return _key_gap(near, key)

        ranked = sorted(on_frame, key=lambda f: (distance(f), order[f]))
        # SPEND ONLY ON THE CLOSEST BAND. With budget left over it would otherwise keep filling from
        # pages that are alphabetically nowhere near the name — reads that cannot hit, charged to his
        # subscription, and reported afterwards as part of a clean negative. If a page brackets the
        # name, pages that do not are not worth a single call.
        best = distance(ranked[0])
        ranked = [f for f in ranked if distance(f) <= best + 0.05]
        picked, seen_pos = [], set()
        by_pos = {i: f for f, i in order.items()}
        for f in ranked:
            if len(picked) >= MAX_PER_REEL:
                break
            for pos in (order[f], order[f] - 1, order[f] + 1):
                if pos in by_pos and pos not in seen_pos and len(picked) < MAX_PER_REEL:
                    seen_pos.add(pos)
                    picked.append(by_pos[pos])
        for f in sorted(picked):
            out.append((reel, os.path.join(path, f), f))
        if len(out) >= MAX_PER_NAME:
            break
    return out[:MAX_PER_NAME]


def _key_gap(a, b):
    """How far apart two sort keys are alphabetically, in [0, 1]. Cheap and monotonic — it only has
    to RANK frames, never measure anything a reader will see."""
    n = min(len(a), len(b))
    for i in range(n):
        if a[i] != b[i]:
            return 1.0 - (i / float(max(n, 1))) * 0.9
    return 0.1 if len(a) != len(b) else 0.0


def hunt(held_names, evidence, hist_dir, read_page, kind="chronicle-uniques", log=None):
    """Read the targeted frames and return {name: [new sightings]}.

    `read_page(path, kind)` is the reader — injected so this module never decides how a page is read
    and the tests never touch a live model. Only sightings of a HUNTED name are returned; anything
    else the page happens to show is left to the ordinary sweep, which is the thing that owns it.
    """
    found = {}
    reads = 0
    for name in held_names:
        targets = targets_for(name, evidence, hist_dir)
        if log:
            log("hunting %-30s %d frame(s) across %d reel(s)"
                % (name, len(targets), len({t[0] for t in targets})))
        for reel, path, frame in targets:
            try:
                page = read_page(path, kind)
            except Exception as exc:
                if log:
                    log("   read failed %s: %s" % (frame, exc))
                continue
            reads += 1
            names = [str(it.get("name") or it) for it in ((page or {}).get("items") or [])]
            if any(_sort_key(n) == _sort_key(name) for n in names):
                found.setdefault(name, []).append(
                    {"reel": reel, "frame": frame, "lane": (page or {}).get("lane") or "claude",
                     "conf": (page or {}).get("conf", 0.7)})
                if log:
                    log("   HIT %s in %s" % (name, reel))
                break   # one other-reel hit is the tag; a second costs money and adds nothing
    if log:
        log("hunt done: %d read(s), new sightings for %d name(s)" % (reads, len(found)))
    return found
