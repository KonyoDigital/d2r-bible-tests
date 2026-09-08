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

#: ══ v#### — THE FOUR ROUTES, AND WHY A ZONE IS NOT ONE ════════════════════════════════════════
#:
#: ⚠⚠ MEASURED 2026-09-08: `subTemplate` WAS COMPUTED AND REACHED NOTHING. v2709 taught this file
#: to say `chronicle · uniques` and `stash · gems`, and a grep for the name across every .py, .html
#: and .js in the tree returned its own definition on line 305 and its own test — no other reader,
#: anywhere. printer.py built its TEMPLATE station off `zone`, so CHRONICLE stayed ONE bucket
#: downstream and a chronicle-SETS reel and a chronicle-UNIQUES reel were indistinguishable to
#: every supervisor that exists. The distinction was correct, and it was thrown away one line after
#: it was made. [[the-unjoined-end]] [[plumbing-with-no-tap]]
#:
#: A ZONE answers WHERE a reel goes — three of them, from ZONE_ORDER. A ROUTE is the individual
#: logic it goes down once it is there, which is his own framing: *"changing routes individually
#: and accordingly relevant to that specific routed reel"*. There are FOUR, because the CHRONICLE
#: zone is read two entirely different ways.
#:
#: (route, zone, ledger). The third member is the LEDGER that tells two chronicle routes apart, and
#: None where the zone alone names the route. ★ IT INVENTS NO VOCABULARY: the zones are
#: ZONE_ORDER's, and `sets`/`uniques` are tv_diablo's own `chronicleTab` values, the ones
#: chron_visit_flush writes onto a visit row at session close.
ROUTES = (
    ("stash",               "STASH",     None),
    ("chronicle · sets",    "CHRONICLE", "sets"),
    ("chronicle · uniques", "CHRONICLE", "uniques"),
    ("inventory",           "INVENTORY", None),
)


def routes_of(row):
    """Every one of the FOUR routes this reel exercised. -> list[str]

    Usually one, and deliberately not forced to be. A session that opened BOTH chronicle ledgers
    exercised BOTH routes and says so; picking a single winner would invent a preference nobody
    expressed, and dropping the second would hide a route from its own supervisor.

    ⚠⚠ AN EMPTY LIST IS NOT A FAULT AND MUST NEVER BE READ AS ONE. A RUN reel, an UNKNOWN reel, and
    a CHRONICLE reel whose ledger nobody ever wrote down all return [] — and only the last of those
    is even about the chronicle routes. "Nobody recorded which page was open" and "the router
    dropped it" are opposite facts; `route_census` below is the one place they are told apart, and
    it needs the raw list to do it. [[unknown-stays-unknown]]
    """
    zone = str((row or {}).get("zone") or "")
    ledgers = {str(x).strip().lower() for x in ((row or {}).get("ledgers") or []) if str(x).strip()}
    out = []
    for name, z, disc in ROUTES:
        if zone != z:
            continue
        if disc is None or disc in ledgers:
            out.append(name)
    return out


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
        # ⚠⚠ v2709 — THE CHRONICLE'S LEDGER, WHICH THIS STATION COULD NEVER NAME.
        # `tabs` below is deliberately STASH-ONLY (see the comment further down: "a tab is
        # evidence about WHICH stash panel was open"), so a CHRONICLE reel resolved to the bare
        # word "chronicle" while every stash reel resolved to "stash · gems/personal". Four of
        # his six MINI_FOCUSES got a tab and the two chronicle ones reached the doorstep — which
        # is exactly what he checked for: ".mini-foc ... the template and classifier".
        #
        # ⚠ THE DATA WAS THERE THE WHOLE TIME, and I eliminated this route twice before finding
        # it. tv_diablo asks for `chronicleTab` on EVERY frame, and v1689's chron_visit_flush
        # writes a {lane:'chronicle', kind:'visit'} row carrying the LEDGER at session close.
        # MEASURED on his ring: 13 visit rows across 12 sessions — uniques 9, sets 3, one unknown.
        # No frame read, no new intake field, no image decoding near the snapshot path.
        #
        # ⚠ AND THE ONE CHRONICLE REEL ON HIS SHELF TODAY ANSWERS UNKNOWN, CORRECTLY.
        # s_1786385768689_67392 is named in chron_visit_flush's own docstring: 8 deep frames,
        # chronicleTab='uniques', and ZERO visit rows written, because the state machine only
        # closed a visit on the way OUT and he looked at the Chronicle LAST. v1689 fixed that at
        # session close; this reel predates the fix. An empty answer here is nobody-recorded, not
        # nothing-was-open. [[unknown-stays-unknown]]
        _ledgers = sorted({str(r.get("ledger") or r.get("chronicleTab") or "").strip().lower()
                           for r in (by_session.get(_sid) or [])
                           if (r.get("lane") == "chronicle" and r.get("kind") == "visit")
                           or (r.get("lane") == "deep" and str(r.get("chronicleTab") or "").strip())}
                          - {""})
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
        _row = {"reel": name, "template": template, "zone": zone, "why": zwhy,
                     "activities": acts, "segments": len(segs),
                     "tabs": tabs,
                     # v2709 — a CHRONICLE reel is refined by its LEDGER, a stash reel by its
                     # TAB. Same shape ("template · what"), two different sources, and neither
                     # can answer for the other.
                     "ledgers": _ledgers,
                     "subTemplate": (
                         (template + " · " + "/".join(_ledgers))
                         if (template and zone == "CHRONICLE" and _ledgers)
                         else ((template + " · " + "/".join(tabs)) if (template and tabs) else template)),
                     "worthReading": worth,
                     "pruneCandidate": candidate}
        # v#### — WHICH OF THE FOUR ROUTES THIS REEL TOOK, on the row itself. Derived from the
        # STRUCTURED fields (`zone`, `ledgers`) immediately above, never by parsing the label:
        # `subTemplate` is what a person reads and `routes` is what a supervisor joins to, and
        # making the second depend on the spelling of the first is how a display change silently
        # re-routes a reel. They are corroborated against each other in `route_census`, which is
        # the only place a disagreement between them can be seen at all.
        # ⚠ `route` IS None WHENEVER THERE IS NOT EXACTLY ONE. A reel that took two routes has not
        # got a single answer, and printing the first would be a preference nobody expressed.
        _row["routes"] = routes_of(_row)
        _row["route"] = _row["routes"][0] if len(_row["routes"]) == 1 else None
        rows.append(_row)
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


def _label_agrees(row, zone, disc):
    """Does this row's LABEL name the route its structured fields gave it? -> (bool, why)

    ⚠⚠ THIS IS A CORROBORATOR, NOT A SECOND DERIVATION, and the difference is the whole reason it
    is worth the lines. `routes_of` reads `zone` and `ledgers`; `subTemplate` is the human label
    built beside them from the SAME facts. Two sites, one truth — so they can only ever disagree
    through an edit that breaks one of them, and that edit is exactly the regression this file was
    written after: v2709 taught the label to name the ledger, NOTHING consumed it, and nothing
    anywhere would have noticed it falling back to the bare word `chronicle`. The label is the half
    that reaches a screen; the census is the half a supervisor joins to. Where they meet is the
    only place either one can be caught.
    """
    sub = row.get("subTemplate")
    if not isinstance(sub, str) or not sub.strip():
        return False, "carries no subTemplate at all, so nothing on a screen can name its route"
    head, _sep, tail = sub.partition(" · ")
    if head.strip() != zone.lower():
        return False, ("its label starts %r, which is not the %s zone it was routed into"
                       % (head.strip()[:30], zone))
    if disc is None:
        return True, ""
    parts = {p.strip().lower() for p in tail.split("/") if p.strip()}
    if disc not in parts:
        return False, ("its label is %r and does not name the %s ledger it carries — the "
                       "distinction was computed and then dropped before it reached a screen"
                       % (sub[:40], disc))
    return True, ""


def route_census(reading=None, river=None):
    """Each of the FOUR routes, ALONE. -> dict

    ⚠⚠ THE DEFECT THIS EXISTS FOR: NOTHING COULD GO RED FOR ONE ROUTE. Measured 2026-09-08 across
    console_doctor's fifty rows, the ones that touch this territory are `extraction lanes`, `vault
    stores`, `vault proposal`, `read names lane` and `names banked` — and not one of them is
    per-route. chronicle-sets and chronicle-uniques were indistinguishable to every supervisor in
    the system, and inventory and stash shared one vault bucket. If exactly one route died,
    everything stayed green. A supervisor that cannot name which of four things broke is not
    supervising four things. [[the-unjoined-end]] [[zero-needs-a-denominator]]

    THREE STATES, and only one of them is a pass:
        OK       reel(s) came out on this route here, and every one of them is labelled to match
        BROKEN   a reel carries this route's evidence and did NOT come out on it, or came out on
                 it under a label that does not name it — the join dropped
        UNKNOWN  no reel on this shelf carries this route's evidence, so NOTHING has been shown
                 about it here

    ⚠⚠ AND UNKNOWN IS THE ANSWER HIS OWN SHELF GIVES FOR HALF OF THEM. Measured the day this was
    written, over 49 reels: STASH 11, INVENTORY 2, CHRONICLE 1 — and that single chronicle reel
    recorded NO ledger, so `chronicle · sets` and `chronicle · uniques` are each taken by ZERO
    reels. A row that only ever reads his live store would be green forever and prove nothing;
    UNKNOWN says so out loud, and the gate supplies the input his footage does not.
    [[gate-blind-to-unexercised-input]] [[unknown-stays-unknown]]

    `reading` is a templates() answer. Passing one in is how the printer gets this for free from
    the snapshot it already took — the river walk must not happen twice on a hot path (v2692).
    """
    order = [n for n, _z, _d in ROUTES]
    if reading is None:
        reading = templates(river=river)
    if not isinstance(reading, dict):
        reading = {"rows": None,
                   "why": "the reading was a %s, not a templates() answer"
                          % type(reading).__name__}
    rows = reading.get("rows")
    if rows is None:
        # ⚠ EVERY RETURN CARRIES EVERY KEY, INCLUDING ALL FOUR ROUTES — REG-546's law. A consumer
        # reading routes["stash"]["state"] must not raise on exactly the path that means nothing
        # was established, and a census that SHRINKS when it fails would read as three routes.
        why = str(reading.get("why") or "the template reading carried no rows")
        return {"ok": False, "state": "UNKNOWN", "order": order, "walked": None,
                "broken": [], "unproven": list(order),
                "routes": {n: {"route": n, "zone": z, "ledger": d, "state": "UNKNOWN",
                               "reels": None, "inZone": None, "broken": 0, "unnamed": None,
                               "sample": [],
                               "why": "the template reading could not be used, so nothing at all "
                                      "is known about this route: %s" % why[:150]}
                           for n, z, d in ROUTES},
                "why": "the four routes are UNKNOWN, not clean — %s" % why[:200]}

    out = {}
    for name, zone, disc in ROUTES:
        took = [r for r in rows if name in (r.get("routes") or [])]
        in_zone = [r for r in rows if str(r.get("zone") or "") == zone]
        broken, unnamed = [], []
        for r in in_zone:
            ledgers = {str(x).strip().lower() for x in (r.get("ledgers") or []) if str(x).strip()}
            has_evidence = (disc is None) or (disc in ledgers)
            if not has_evidence:
                # a CHRONICLE reel whose ledger nobody wrote down. NOT this route's business and
                # NOT a fault — it is the pre-v1689 shape, named so the zero has a denominator.
                if disc is not None and not ledgers:
                    unnamed.append(str(r.get("reel") or "?"))
                continue
            if name not in (r.get("routes") or []):
                broken.append("%s carries the evidence for this route and was not routed onto it"
                              % str(r.get("reel") or "?")[:40])
                continue
            agrees, awhy = _label_agrees(r, zone, disc)
            if not agrees:
                broken.append("%s %s" % (str(r.get("reel") or "?")[:40], awhy))
        if broken:
            state = "BROKEN"
            why = ("%d reel(s) carry this route's evidence and did not come out on it intact: %s"
                   % (len(broken), "; ".join(broken[:3])[:260]))
        elif took:
            state = "OK"
            why = ("%d of %d reel(s) on this shelf came out on this route, and every one of them "
                   "is labelled to match" % (len(took), len(rows)))
        else:
            state = "UNKNOWN"
            if disc is None:
                why = ("no reel on this shelf is in the %s zone, so this route is UNPROVEN here — "
                       "unexercised, which is not the same fact as healthy. %d reel(s) were "
                       "walked." % (zone, len(rows)))
            else:
                why = ("no reel on this shelf carries a %s ledger, so this route is UNPROVEN here "
                       "— unexercised, which is not the same fact as healthy. %d reel(s) are in "
                       "the %s zone and %d of them recorded no ledger at all (nobody wrote one "
                       "down; that is not a broken route). A gate has to supply this input, "
                       "because his footage does not."
                       % (disc, len(in_zone), zone, len(unnamed)))
        out[name] = {"route": name, "zone": zone, "ledger": disc, "state": state,
                     "reels": len(took), "inZone": len(in_zone), "broken": len(broken),
                     "unnamed": len(unnamed),
                     "sample": [str(r.get("reel") or "?") for r in took[:3]],
                     "why": why}

    bad = [n for n in order if out[n]["state"] == "BROKEN"]
    dark = [n for n in order if out[n]["state"] == "UNKNOWN"]
    state = "BROKEN" if bad else ("PARTIAL" if dark else "OK")
    # ⚠⚠ AN UNPROVEN ROUTE IS NOT AN `ok` ONE, and the two lists stay SEPARATE so nobody has to
    # guess which kind of not-ok they are looking at. lane_health.report counts `unknown` as bad
    # for the same reason and in the same territory: a supervisor that says ok while two of its
    # four subjects were never exercised is the green that lies. On his shelf this is False today
    # and the honest reason is `unproven`, not `broken`. [[unknown-stays-unknown]]
    return {
        "ok": not (bad or dark), "state": state, "order": order, "walked": len(rows),
        "broken": bad, "unproven": dark, "routes": out,
        "why": (("%d of %d route(s) BROKEN: %s. " % (len(bad), len(order), ", ".join(bad)))
                if bad else ("all %d route(s) came out intact. " % len(order) if not dark else
                             "no route is broken. "))
               + (("%d route(s) are UNPROVEN on this shelf (%s) — unexercised, which is never the "
                   "same as healthy." % (len(dark), ", ".join(dark))) if dark else ""),
    }


def main(argv):
    r = templates([a for a in argv if not a.startswith("-")] or None)
    cen = route_census(reading=r)
    if "--json" in argv:
        print(json.dumps(dict(r, routeCensus=cen), indent=2, sort_keys=True, default=str))
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
    print("\n  THE FOUR ROUTES — each one on its own\n")
    for name in cen.get("order") or []:
        row = (cen.get("routes") or {}).get(name) or {}
        mark = {"OK": "\U0001F7E2", "BROKEN": "\U0001F534"}.get(row.get("state"), "\u26aa")
        print("  %s %-22s %-8s %s" % (mark, name, row.get("state"),
                                      str(row.get("why") or "")[:110]))
    print("\n  %s" % cen.get("why"))
    print("\n  %s\n" % r["why"])
    return 0


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
