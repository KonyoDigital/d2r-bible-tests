#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WHAT A REEL *IS*, AND THEREFORE WHERE IT GOES — the printer's missing template layer.

Konyo, 2026-09-04: *"the printer should be architected via templates and techniques for those same
reels to go through the printer we constructed and gets organized and it prunes the IRRELAVANT
reels... all unified logic for the reels.. just the diffrence is the reel itself and the image
relating it should get routed accordingly to its individual logic meaning a item with a tooltip
image within the stash.. gets the stash route... a farming or a run... is just a run and farming
route.. so also to its own individual logic."*

⚠⚠ WHY THIS EXISTS, MEASURED 2026-09-04. The printer's ROUTE station could not see what a reel IS.
It reported `content` (what the reel HOLDS — zero-pages) or `policy` (age, or a suite opening it),
and on his forty reels that split 28/12. Neither answer is a TEMPLATE. Meanwhile `reel_segments`
has classified reels into activities since v2343 — measured on his own footage as *gameplay 212 ·
transition 27 · stash 13 · town 13 · inventory 4 · chronicle 3* — and has four production
consumers, **none of them the printer**. Two halves, each built and correct, never joined.
[[the-unjoined-end]] [[plumbing-with-no-tap]]

★ IT INVENTS NO VOCABULARY. The activities are `reel_segments`'s, the lane mapping is
`reel_segments._ACTIVITY_LANE`, and the journal ring is `control_app._journal_ring()` — whose own
docstring records v1493, where eleven sites read one journal and ten of them hardcoded the path, so
a harness that believed it was isolated read his real farming nights. A second copy of any of those
is exactly [[copy-drift]] §1. This file asks the owners and arranges the answers.

★ AND IT DELETES NOTHING. A reel whose template yields no extractable zone is reported as a PRUNE
CANDIDATE — a row on paper. Nothing here removes a byte, and `prune` stays off by its own flag.

⚠⚠ UNKNOWN IS NEVER A PRUNE CANDIDATE, and that is the single most important line in this file. A
reel the segmenter cannot classify has NOT been shown to be irrelevant — it has not been read. Those
are opposite facts and collapsing them would route unexamined footage to the deleter.
[[unknown-stays-unknown]]

    python3 tv/reel_templates.py            # every reel, its template and its zone
    python3 tv/reel_templates.py --json
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

#: activity -> (zone, why). THE ORDER IS THE PRIORITY and it is his: *"an item with a tooltip image
#: within the stash.. gets the stash route"*. A reel carrying several activities takes the first
#: match reading down. Every activity name here is `reel_segments`'s, never a new spelling.
ZONE_ORDER = (
    ("stash", "STASH",
     "the STASH was open — the ONLY activity reel_segments maps to a container lane "
     "(_ACTIVITY_LANE), so this is the one zone that can grant possession"),
    ("chronicle", "CHRONICLE",
     "a Chronicle page was open — the chronicle routes own what is read here"),
    ("inventory", "INVENTORY",
     "the INVENTORY was open. ⚠ HELD IS NOT OWNED: v2346 withdrew `inventory -> inventory` "
     "because it granted a container lane to anything merely being carried. Extractable, "
     "but it may not grant ownership on its own"),
)

#: activities that mean the reel is a RUN — farming, walking, loading. Nothing to extract from
#: them, and that is not a fault: it is what most of his footage IS.
RUN_ACTIVITIES = ("gameplay", "town", "transition")


def _segments_for(reel, rows_by_session):
    """-> (segments, why). Asks reel_segments; never re-derives a timeline."""
    import reel_segments as RS
    sid = str(reel or "")
    sid = sid[len("reel_"):] if sid.startswith("reel_") else sid
    rows = rows_by_session.get(sid) or []
    if not rows:
        return [], "no journal row carries this reel's sessionId"
    try:
        return RS.segments(rows), ""
    except Exception as e:
        return [], "reel_segments would not answer (%s)" % str(e)[:80]


#: (key -> (rows_by_session, why)). ONE entry; the journal is the only input.
_CACHE = {"key": None, "val": None}


def _ring_key(paths):
    """A cache key over the ring. -> tuple

    ⚠⚠ EVERY PATH, ITS mtime AND ITS SIZE — never a fold. v2484 shipped a key that ran every
    mtime through `max()`, so touching one file left the key byte-identical in three modules and
    the cache answered with stale content. A key that loses which file changed is not a key.
    ⚠ AND THE COMMENT HERE WAS WRONG BEFORE IT SHIPPED. The first cut said size is carried
    "because a same-second rewrite of equal length is exactly the edit an mtime-only key cannot
    see" — but this reads `st_mtime_ns`, at NANOSECOND resolution, which catches a same-second
    rewrite perfectly well. That sentence was true of a second-resolution mtime and false of the
    code beneath it, which is v2565's scar exactly. The honest reason to carry size: some
    filesystems (notably network mounts) report a coarse or lazily-updated mtime, and size is a
    second, independent signal that costs nothing in the same stat call.
    """
    out = []
    for path in paths:
        try:
            st = os.stat(path)
            out.append((path, st.st_mtime_ns, st.st_size))
        except Exception:
            out.append((path, None, None))
    return tuple(out)


def _journal_rows():
    """Every journal row, grouped by sessionId. -> (dict, why)

    ⚠ CACHED ON THE RING'S OWN mtimes. Measured 2026-09-04: this walk takes 2.51s against
    printer.stream()'s 0.04s, and the printer runs on every heart open. A 2.5s answer on a hot
    path is the shape of [[poll-slower-than-its-interval]], which once saturated his Mac with a
    172s job answered every 12s. The cache is invalidated by the journal changing and by nothing
    else, so a new recording is picked up and a re-read costs nothing.

    ⚠ THE RING, NOT THE LIVE FILE. control_app._journal_ring() is asked for the paths because it
    owns them; re-deriving `HERE/sessions.jsonl` here would be the eleventh hardcoded site its own
    docstring exists to prevent.
    """
    try:
        import control_app as CA
        paths = [p for p in (CA._journal_ring() or []) if os.path.isfile(p)]
    except Exception as e:
        return {}, "the journal ring could not be resolved (%s)" % str(e)[:80]
    if not paths:
        return {}, "the journal ring resolved to no existing file"
    key = _ring_key(paths)
    if _CACHE["key"] == key and _CACHE["val"] is not None:
        return _CACHE["val"]
    out = {}
    for path in paths:
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        r = json.loads(line)
                    except Exception:
                        continue
                    sid = str((r or {}).get("sessionId") or "").strip()
                    if sid:
                        out.setdefault(sid, []).append(r)
        except Exception:
            continue
    _CACHE["key"], _CACHE["val"] = key, (out, "")
    return out, ""


def templates(reels=None, river=None):
    """Every reel, what it IS, and the zone that follows. -> dict

    ⚠ v2692 — `river` IS AN INJECTION, NOT A CACHE. reel_river.river() walks reel_retention.plan()
    over every reel directory, and printer.stream() used to cause THREE independent walks per call
    (its own, this one, and extract_gap's). Measured: /api/heart cold took 19.54s, against a render
    gate that allows 10s warmup + a 12s activate poll — so the heart panel could not populate in
    time and the push was BLOCKED with "the panel could not be ACTIVATED". Passing one snapshot in
    is the fix; the default keeps every standalone caller working exactly as before.
    ⚠ It must stay a PARAMETER rather than a module-level memo: a stale river held across calls is
    how a station starts reporting a reel that is no longer on disk. [[stale-reading]]
    """
    import reel_river as RR
    try:
        riv = river if river is not None else RR.river()
    except Exception as e:
        return {"ok": False, "state": "UNKNOWN", "rows": [], "counts": {},
                "why": "reel_river would not answer (%s) — UNKNOWN, not an empty shelf"
                       % str(e)[:80]}
    names = [str(r.get("reel") or "") for r in (riv.get("rows") or [])
             if str(r.get("reel") or "").strip()]
    if reels:
        names = [n for n in names if any(x in n for x in reels)]
    by_session, why = _journal_rows()
    # ⚠⚠ v2573 — THE MODULE THAT OWNS THE 80/20 QUESTION WAS NEVER ASKED. retro_triage exists
    # because of his words — *"the filter and templates built should be disposing the 70%
    # unrelevant reels"* — and `worth_reading()` answers it per reel in three states, where None
    # means NOT SURVEYED and explicitly never False ("a reel nobody has looked at must not be
    # skipped as if it had been looked at and found empty; that is how footage gets abandoned").
    # The printer classified templates without ever consulting it. [[the-unjoined-end]]
    try:
        import retro_triage as _RTG
    except Exception:
        _RTG = None

    rows, counts = [], {}
    for name in sorted(names):
        segs, sw = _segments_for(name, by_session)
        # ⚠⚠ v2582 — THE SUB-TEMPLATE WAS RECORDED AND THE ROUTER IGNORED IT. His list:
        # *"stash/runes/gems each have their template.. also test those individually..
        # runes/gems/materials... then we have stash then we have INVENTORY/STASH.. then we have
        # CHRONICLES"*. Measured on his store: `stashTab` is on the deep rows with real counts —
        # shared 12, personal 8, runes 8, materials 8, gems 6 — and reel_segments does not carry
        # it into a segment, so nothing downstream could route on it. A stash reel and a RUNE
        # stash reel were the same thing to this module.
        #
        # Taken from the RAW rows this function already holds, not by widening reel_segments:
        # a segment is a span of time and a tab is a property of a read, and forcing one into
        # the other would make the segmenter answer a question it was not asked. [[copy-drift]]
        _sid = name[len("reel_"):] if name.startswith("reel_") else name
        tabs = sorted({str(r.get("stashTab") or "").strip()
                       for r in (by_session.get(_sid) or [])
                       if r.get("lane") == "deep" and str(r.get("stashTab") or "").strip()})
        acts = sorted({str(s.get("activity") or "").lower() for s in segs
                       if str(s.get("activity") or "").strip()})
        if not acts:
            # ⚠⚠ v2604 — "THE SEGMENTER RETURNED NO ACTIVITY" NAMED THE WRONG THING. Measured on
            # his shelf: 14 of 40 reels are UNKNOWN here, and for every one of them the journal
            # holds **ZERO deep rows** — while every classified reel holds 1 to 9. Their footage is
            # NOT gone: those 14 carry 22 to 2,385 frames on disk. Nothing has ever READ them.
            #
            # The old sentence sent a reader to the segmenter, which is working perfectly and has
            # simply been handed nothing. Three different states were collapsed into one wording,
            # and only the first of them is anybody's fault:
            #     no rows at all       -> nothing has read this reel
            #     rows but none deep   -> read shallowly, never deeply
            #     deep rows, no acts   -> read, and the reads carry no activity
            # A label that points at the wrong component is how a working part gets investigated
            # and a missing input does not. [[label-outlived-referent]] [[unknown-stays-unknown]]
            _all_rows = by_session.get(_sid) or []
            _deep = [r for r in _all_rows if r.get("lane") == "deep"]
            if not _all_rows:
                _why = ("NOTHING HAS READ THIS REEL - the journal holds no row for it at all. Its "
                        "frames are on disk; no reader has produced anything from them. This is a "
                        "missing input, not a fault in the segmenter")
            elif not _deep:
                _why = ("this reel has %d journal row(s) and NONE on the deep lane, so the "
                        "segmenter had nothing to segment - it was read shallowly and never "
                        "deeply" % len(_all_rows))
            else:
                _why = ("this reel has %d deep row(s) and none of them carries an activity, so "
                        "the reads exist and say nothing about what was open"
                        % len(_deep))
            zone, zwhy, template = "UNKNOWN", (sw or why or _why), None
        else:
            hit = next(((a, z, w) for a, z, w in ZONE_ORDER if a in acts), None)
            if hit:
                template, zone, zwhy = hit[0], hit[1], hit[2]
            elif all(a in RUN_ACTIVITIES for a in acts):
                template, zone = "run", "RUN"
                zwhy = ("only %s — a farming run. Nothing to extract, and that is what most "
                        "footage IS, not a fault" % ", ".join(acts))
            else:
                template, zone = None, "UNKNOWN"
                zwhy = ("activities %s match no declared zone — UNKNOWN rather than guessed"
                        % ", ".join(acts))
        # ⚠⚠ ONLY A REEL PROVEN TO BE A RUN IS A PRUNE CANDIDATE. UNKNOWN never is.
        # ⚠ THREE STATES, AND None IS NOT False. A reel the survey never reached is UNSURVEYED,
        # which is a different fact from surveyed-and-empty and must never be treated as one.
        worth = None
        if _RTG is not None:
            try:
                worth = _RTG.worth_reading(name)
            except Exception:
                worth = None

        # ⚠⚠ AND THE SURVEY CAN ONLY EVER *SPARE* A REEL HERE, NEVER CONDEMN ONE. A reel proven
        # to be a run is a candidate; if the survey says it nonetheless holds panels, that is
        # evidence it is worth keeping and the candidacy is withdrawn. The reverse is deliberately
        # NOT done: "surveyed, nothing in it" does not make a STASH reel disposable, because the
        # template already said there is something here to extract. Two readers disagreeing must
        # resolve toward keeping footage. [[unknown-stays-unknown]]
        candidate = (zone == "RUN")
        if candidate and worth is True:
            candidate = False
            zwhy += ("  ⚠ the survey says this run DOES hold panels, so it is not a prune "
                     "candidate after all — the survey spares it")

        # ⚠ THE TAB REFINES THE TEMPLATE, IT NEVER OVERRIDES THE ZONE. A tab is evidence about
        # WHICH stash panel was open, not about whether the reel is a possession moment — that is
        # still the activity's job. Naming it here lets a reader see `stash · runes` without the
        # routing changing underneath them. An empty list means no read recorded a tab, which is
        # NOT the same as "no tab was open". [[unknown-stays-unknown]]
        rows.append({"reel": name, "template": template, "zone": zone, "why": zwhy,
                     "activities": acts, "segments": len(segs),
                     "tabs": tabs,
                     "subTemplate": ((template + " · " + "/".join(tabs))
                                     if (template and tabs) else template),
                     "worthReading": worth,
                     "pruneCandidate": candidate})
        counts[zone] = counts.get(zone, 0) + 1

    unknown = counts.get("UNKNOWN", 0)
    return {
        "ok": bool(rows), "rows": rows, "counts": counts, "walked": len(rows),
        "unknown": unknown, "pruneCandidates": sum(1 for r in rows if r["pruneCandidate"]),
        "state": ("UNKNOWN" if not rows else ("PARTIAL" if unknown else "CLASSIFIED")),
        "zones": [z for _a, z, _w in ZONE_ORDER] + ["RUN", "UNKNOWN"],
        "why": (("%d reel(s) classified by TEMPLATE. %s ⚠ A reel is a PRUNE CANDIDATE only when it "
                 "is PROVEN a run; %d are UNKNOWN and none of those is a candidate — not-read and "
                 "not-relevant are opposite facts. Nothing here deletes anything."
                 % (len(rows),
                    " · ".join("%s %d" % (k, v) for k, v in sorted(counts.items())),
                    unknown))
                if rows else "no reel reached the template router"),
    }


def main(argv):
    r = templates([a for a in argv if not a.startswith("-")] or None)
    if "--json" in argv:
        print(json.dumps(r, indent=2, sort_keys=True, default=str))
        return 0
    print("\nREEL TEMPLATES — what each reel IS, and the zone that follows\n")
    if not r["ok"]:
        print("  %s\n" % r["why"])
        return 0
    print("  %s · %d reel(s)\n" % (r["state"], r["walked"]))
    for z in r["zones"]:
        if r["counts"].get(z):
            print("  %-10s %d" % (z, r["counts"][z]))
    print()
    for row in r["rows"][:60]:
        print("  %-34s %-9s %-10s %s" % (row["reel"][:34], row["template"] or "-",
                                         row["zone"], ",".join(row["activities"]) or "-"))
    print("\n  %s\n" % r["why"])
    return 0


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
