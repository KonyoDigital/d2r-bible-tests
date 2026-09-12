#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WHY A REEL CANNOT BE EXTRACTED — per reel, and the gap that is RECOVERABLE.

Konyo, 2026-09-04: *"whatever needs to be built and architecured so this printer works correctly
and routes those reels and extract them via the console"*, and earlier: *"images coming through
with tooltips or without is also a key information data thats almost always needed for witnesses
and item slot identity"*.

⚠⚠ THE CONTRADICTION THIS EXISTS TO PUBLISH. Two measurements of "can we extract from this reel"
disagree, and BOTH are right about their own question:

    printer_reach   0 of 30 seals satisfy the extraction contract — 22 blocked because
                    "the sweep never extracted name", 8 predate the contract.
                    -> the printer's EXTRACT station said UNREACHABLE for all 40 reels.

    the journal     472 item names were actually READ, across 52 sessions.
                    15 of his 40 live reels yielded at least one.

    OVERLAP         13 sessions have BOTH a seal AND reads that yielded names.

⚠ v2772 — AND "THE NAMES EXIST" IS NOT THE SAME AS "A HOLDING EXISTS". The overlap below counts
raw names; `holding_possible()` is the law that says which of them the extraction contract can
actually take, and on his store it removes the single loudest row on this report — 45 Chronicle
checklist entries that were being reported as a join anyone was owed. Read that docstring before
trusting any RECOVERABLE figure here.

**For those 13 the names EXIST and the seal does not carry them.** That is a JOIN, not a capture
problem — which matters because REG-340 ruled the missing-name case a capture change ("the reel
must film the character panel"). REG-340 is about the CHARACTER name on the character panel; this
is about ITEM names, which the reader is demonstrably getting. Different field, different answer,
and conflating them would have left a recoverable gap looking permanent.

★ IT WRITES NOTHING, AND ESPECIALLY NOT A SEAL. A seal is the record frame_authority exists to
protect; back-filling one from here would forge the certification it stands for. This REPORTS the
gap so the fix can be made where the seal is WRITTEN, with the numbers to size it.

    python3 tv/extract_gap.py
    python3 tv/extract_gap.py --json
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

#: the states a reel's extractability can be in, and they are NOT a scale — each is a
#: different fact and the difference decides what to do about it.
RECOVERABLE = "RECOVERABLE"   # the seal lacks the name; the journal HAS it. A join.
NO_NAMES = "NO_NAMES"         # sealed, and the reader never got a name either. Capture.
UNSEALED = "UNSEALED"         # read (maybe named) but no seal at all yet.
#: ⚠⚠ v2772 — THE FIFTH FACT, AND IT WAS WEARING RECOVERABLE'S CLOTHES. Sealed, names WERE read,
#: and not one of them could ever become a holding — so there is no join owed and no footage owed
#: either. See holding_possible() for the law and the measurement that forced it.
NOT_A_HOLDING = "NOT_A_HOLDING"
UNKNOWN = "UNKNOWN"           # nobody could be asked. Never a verdict.


def _session_of(reel):
    r = str(reel or "").strip()
    return r[len("reel_"):] if r.startswith("reel_") else r


#: ⚠⚠ v2583 — WHERE A NAME WAS READ DECIDES WHAT CAN BE EXTRACTED FROM IT, and nothing carried
#: that. His words: *"if its a FLOOR ITEM with no stash/inventory open then obviously it cant be
#: in the same exact route as the tooltip image reel that is a tooltip within the stash/inventory"*.
#:
#: MEASURED on his store, over all 472 names the readers have actually produced:
#:
#:     PANEL      110   stash 71 · inventory 39   — a container was open, so a SLOT can exist
#:     FLOOR      208   gameplay 200 · loot 6 · town 2 — on the ground; there is no cell to name
#:     CHRONICLE  154   a checklist page, and the code already refuses it as possession
#:
#: So 362 of 472 arrived with NO container open. Asking slot_identity about those is asking for a
#: coordinate that cannot exist — which is the difference between "not extracted yet" and "not
#: extractable", and only one of those is work owed. [[unknown-stays-unknown]]
#:
#: ⚠ AND THE ROUTING CONFLICT I EXPECTED FROM THIS IS NOT THERE. I predicted RUN-zone reels would
#: be full of floor names and offered to the deleter. Measured: of 12 RUN reels exactly ONE
#: yielded names (two of them), and the survey had already spared it. Reported as a negative
#: rather than built into a fix for a problem his shelf does not have.
PANEL_SCENES = ("stash", "inventory")
FLOOR_SCENES = ("gameplay", "loot", "town", "transition")


def holding_possible(counts, names_known=True):
    """Can the names read for this session become the holding the contract asks for? -> (bool|None, why)

    ⚠⚠ v2772 — THE SCENARIO WAS COMPUTED AND THE VERDICT NEVER ASKED FOR IT, and that turned the
    LOUDEST number on this report into a false one. v2583 built the PANEL/FLOOR/CHRONICLE taxonomy
    forty lines above the state machine, wrote down that a Chronicle name is "a checklist of items
    he mostly does not own, never a holding", and then the state machine decided RECOVERABLE on
    `has_seal and n` — the raw name count, scenario unread. [[the-unjoined-end]]

    MEASURED on his store the moment the two were put side by side:

        reel_s_1786385768689_67392   names 45   panel 0 · floor 0 · CHRONICLE 45   -> RECOVERABLE
        the other three sealed+named  names 10   panel 10                          -> RECOVERABLE

    45 of the 55 names the report called "a JOIN to fix where the seal is written" — 82% of the
    whole recoverable gap — are Chronicle grid entries (Amulet, Ancient Sword, Andariel's Visage,
    Arm of King Leoric…). He owns almost none of them. Backfilling those into a possession seal
    would not be a join; it would invent 45 holdings.

    ⚠ AND A SECOND READER ALREADY DISAGREED, using this module's OWN constant. `read_names_lane`
    filters deep rows to `EG.PANEL_SCENES` and produces evidence for 22 sessions — and
    s_1786385768689_67392 is NOT one of them. Two checks over the same reel, opposite answers, and
    the one that was wrong was the one on the report. [[feedback-contradiction-is-the-finding]]

    THE LAW, and it is the contract's own words rather than a new rule. EXTRACTION_CONTRACT wants
    `location` = *"WHERE it was — the container and the cell box inside it (his slot identity)"*.

        PANEL      a container was open, so a cell exists          -> a holding can exist
        FLOOR      on the ground; there is no cell to ask for      -> no location, so no holding
        CHRONICLE  a checklist page, never a possession            -> no holding at all

    So the predicate is `panel > 0`, and it is ONE predicate covering both refusals rather than two
    that could drift. ⚠ EXERCISED BY HIS DATA ON THE CHRONICLE SIDE ONLY: of the four sealed reels
    carrying names, 1 is chronicle-only and 0 are floor-only. The floor arm is real law and is
    currently unwitnessed on this store — said out loud rather than left to look covered.
    [[gate-blind-to-unexercised-input]]

    ⚠ `names_known=False` returns None, never False. A venue whose journal ring cannot be read has
    not measured zero holdings; nobody asked. [[unknown-stays-unknown]]
    """
    if not names_known:
        return None, ("the journal ring could not be read, so whether any name here could become a "
                      "holding is UNKNOWN — not zero")
    c = counts if isinstance(counts, dict) else {}
    panel = int(c.get("panel") or 0)
    floor = int(c.get("floor") or 0)
    chron = int(c.get("chronicle") or 0)
    if panel:
        return True, ("%d name(s) were read with a container OPEN, so a cell box exists for them "
                      "and the contract's `location` can be satisfied" % panel)
    if not (floor or chron):
        return False, "no item name was read for this session, so there is nothing to make a holding of"
    bits = []
    if chron:
        bits.append("%d on a Chronicle page (a checklist of items he mostly does not own)" % chron)
    if floor:
        bits.append("%d on the floor (no container, so no cell to name)" % floor)
    return False, ("every name here was read with NO container open — %s. The contract wants a "
                   "location and there is none to take, so this is not a join that anyone is "
                   "owed." % " and ".join(bits))


def _named_sessions():
    """sessionId -> how many item names its DEEP reads yielded. -> (dict, why)

    ⚠ DEEP LANE ONLY. tv_diablo stamps a provisional label on every OCR row ("never farmed from
    OCR alone"), so counting those would credit the reel with names nobody observed — the same
    exclusion reel_segments makes, and for the same reason.
    """
    try:
        import control_app as CA
        paths = [p for p in (CA._journal_ring() or []) if os.path.isfile(p)]
    except Exception as e:
        return {}, "the journal ring could not be resolved (%s)" % str(e)[:80]
    out = {}
    for path in paths:
        try:
            with io.open(path, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        r = json.loads(line)
                    except Exception:
                        continue
                    if (r or {}).get("lane") != "deep":
                        continue
                    sid = str(r.get("sessionId") or "").strip()
                    if not sid:
                        continue
                    names = [x for x in (r.get("names") or []) if str(x).strip()]
                    if not names:
                        continue
                    cur = out.get(sid) or {"names": 0, "panel": 0, "floor": 0,
                                          "chronicle": 0, "equipped": 0, "contradicted": 0,
                                          "unplaced": 0}
                    for _k in ("equipped", "contradicted", "unplaced"):
                        cur.setdefault(_k, 0)      # older callers built the 4-key shape
                    cur["names"] += len(names)
                    sc = str(r.get("scene") or "").strip().lower()
                    # ⚠⚠ v3043 — `cur["panel"] += len(names)` WAS THE WHOLE DEFECT. One frame carries
                    # ONE `scene` and a LIST of names, so every name inherited the frame's label.
                    # In D2R the stash panel and the inventory are open TOGETHER, so a single frame
                    # legitimately holds items from BOTH containers — and this counted all of them
                    # as whichever panel the frame was called.
                    #
                    # read_names_lane was fixed for exactly this in v2983 and RECORDS the per-item
                    # container in `names_loc`. This module never read it: measured 2026-09-12, it
                    # referenced `loc` zero times and `scene` once. The producer had the right
                    # answer and the classifier ignored it. [[the-unjoined-end]]
                    #
                    # MEASURED on his journal, frame scene / item names_loc:
                    #   stash/inventory 56 · stash/stash 12 · inventory/inventory 31
                    #   inventory/floor 7 · stash/floor 1 · stash/equipped 2 · inventory/equipped 1
                    #   gameplay/floor 199 (agrees) · chronicle/(unplaced) 154
                    # So 11 names that can NEVER be a holding were counted as panel, and 56
                    # inventory items were filed under stash.
                    #
                    # ⚠⚠ HIS RULING, 2026-09-12, and it is the reason `stash` is not a container
                    # here: *"stash/stash there is no such thing.. when stash is open the INVENTORY
                    # IS OPEN at the same time soo stash/inventory is when we stash items..
                    # inventory/inventory is just inventory which is sometimes a place before we
                    # stash the item from inventory to the stash"*. Items already sitting in the
                    # stash are not what gets read. A name the producer placed in `stash` therefore
                    # CONTRADICTS the way the panels actually work, and it is counted as such and
                    # named — never folded into panel, and never silently dropped.
                    # [[feedback-contradiction-is-the-finding]]
                    _loc = r.get("names_loc")
                    _loc = _loc if isinstance(_loc, dict) else {}
                    for _nm in names:
                        _own = str(_loc.get(_nm) or "").strip().lower()
                        if not _own:
                            # ⚠ UNPLACED. The producer did not place this name, so the frame is
                            # all that is known — and that is exactly the chronicle case, where
                            # 154 of 155 unplaced names live. A guess here would be
                            # indistinguishable from a reading. [[unknown-stays-unknown]]
                            # ⚠⚠ AND THE FALLBACK IS NOT UNIFORM, because the two frames do not
                            # know the same thing. A CHRONICLE frame IS its names — the grid is
                            # the list, so the frame defines them and falling back is safe, which
                            # is what keeps his 154 chronicle names classified. A PANEL frame
                            # shows the stash AND the inventory at once, so falling back there
                            # would pick a container by coin-flip and register a holding nobody
                            # observed. An unplaced name in a panel frame stays UNPLACED.
                            # Measured on his journal: 154 of the 155 unplaced names are chronicle
                            # and one is gameplay — ZERO are in panel frames, so this costs him
                            # nothing today and refuses to invent one tomorrow.
                            # [[unknown-stays-unknown]]
                            if sc in PANEL_SCENES:
                                cur["unplaced"] += 1
                            elif sc == "chronicle":
                                cur["chronicle"] += 1
                            elif sc in FLOOR_SCENES:
                                cur["floor"] += 1
                        elif _own == "inventory":
                            cur["panel"] += 1          # his, in hand — stashing or pre-stash
                        elif _own == "stash":
                            cur["contradicted"] += 1   # cannot happen; see his ruling above
                        elif _own == "equipped":
                            cur["equipped"] += 1       # cross-reference only, never authoritative
                        elif _own == "floor" or _own in FLOOR_SCENES:
                            cur["floor"] += 1
                        elif _own == "chronicle":
                            cur["chronicle"] += 1
                    out[sid] = cur
        except Exception:
            continue
    return out, ""


def gap(reels=None, river=None):
    """Per reel: can it be extracted, and if not, is the gap RECOVERABLE? -> dict

    ⚠ v2692 — `river` is the same injection reel_templates.templates() takes, for the same reason:
    printer.stream() caused three independent reel_river.river() walks per call. See that
    docstring for the measurement. Default preserves standalone behaviour.
    """
    try:
        import reel_river as RR
        riv = river if river is not None else RR.river()
    except Exception as e:
        return {"ok": False, "state": UNKNOWN, "rows": [], "counts": {},
                "why": "reel_river would not answer (%s) — UNKNOWN, not an empty shelf"
                       % str(e)[:80]}
    try:
        import frame_authority as FA
        seals, sok = FA.sealed_sessions()
        if not sok or not isinstance(seals, dict):
            seals, swhy = {}, "frame_authority would not report its seals"
        else:
            swhy = ""
    except Exception as e:
        seals, swhy = {}, "frame_authority would not answer (%s)" % str(e)[:80]

    named, nwhy = _named_sessions()
    #: ⚠ v2772 — DID THE JOURNAL ANSWER AT ALL. `_named_sessions` returns ({}, why) on a ring it
    #: could not resolve, and `n` is then 0 for every reel on the shelf — indistinguishable from a
    #: measured zero. This is the denominator the name count never carried.
    names_known = not nwhy
    names_arg = reels
    rows, counts = [], {}
    for r in (riv.get("rows") or []):
        reel = str(r.get("reel") or "").strip()
        if not reel:
            continue
        if names_arg and not any(x in reel for x in names_arg):
            continue
        sid = _session_of(reel)
        _nm = named.get(sid) or {}
        n = int(_nm.get("names") or 0)
        # the SCENARIO this reel's names came from — what extraction may even ask for
        # ⚠⚠ v2590 — THE REASON NAMED THE LEAD AND HID THE REST. A cold review pointed out that
        # the scenario is the FIRST truthy count in priority order while all three counts are
        # published beside it, so a row could read `scenario=PANEL` next to `floorNames=20` with
        # nothing explaining the 20. Measured: 3 of his 40 reels are exactly that, the worst
        # being panel=3 alongside floor=20 — the reason mentioned the 3 and said nothing about
        # the 20. The lead is unchanged and still correct; the sentence now carries every
        # non-zero count so the numbers beside it cannot look unexplained.
        # ⚠ the "also" list EXCLUDES the bucket the sentence just named — the first cut repeated
        # it ("2 read with a container OPEN … also holds 2 in a container"), which reads as two
        # different measurements of the same thing.
        _LEAD = "panel" if _nm.get("panel") else ("floor" if _nm.get("floor") else "chronicle")
        _mix = ", ".join("%d %s" % (_nm[k], n) for k, n in
                         (("panel", "in a container"), ("floor", "on the floor"),
                          ("chronicle", "on a Chronicle page"))
                         if _nm.get(k) and k != _LEAD)
        _also = ("  (and %s — counted, not extractable the same way)" % _mix) if _mix else ""
        if _nm.get("panel"):
            scenario, s_why = "PANEL", ("%d name(s) read with a container OPEN — a slot identity "
                                        "can exist for these%s" % (_nm["panel"], _also))
        elif _nm.get("floor"):
            scenario, s_why = "FLOOR", ("%d name(s) read with NO container open — an item on the "
                                        "ground has no cell, so a slot cannot be asked for%s"
                                        % (_nm["floor"], _also))
        elif _nm.get("chronicle"):
            scenario, s_why = "CHRONICLE", ("%d name(s) read on a Chronicle page — a checklist of "
                                            "items he mostly does not own, never a holding%s"
                                            % (_nm["chronicle"], _also))
        else:
            scenario, s_why = "UNKNOWN", "no name was read for this reel, so no scenario applies"
        # ⚠ v2772 — the scenario now DECIDES rather than merely riding along. One call, one law,
        # used by the state below and published on the row, so a reader and the verdict cannot
        # give different answers about the same reel. [[copy-drift]]
        hold, hwhy = holding_possible(_nm, names_known)
        has_seal = sid in seals
        # ⚠⚠ v2692 — "HAS A SEAL" AND "THE SEAL CERTIFIES THE EXTRACTION" ARE TWO DIFFERENT FACTS,
        # and this file reported only the first, so every reader (including me, all session) took
        # one for the other. MEASURED on his tree: 30 seals on disk, ZERO satisfying
        # EXTRACTION_CONTRACT ('name','location','provenance') — 22 carry an `extracted` list
        # missing 'name', 8 predate the contract and carry none at all.
        # Thirty reels LOOK sealed and none is certified. A SEAL-ALL surface built on `sealed`
        # alone would print 40/40 while certifying nothing, which is the exact conflation
        # frame_authority guards against one layer down: "an unstated fact is an unextracted one".
        # Reported, never inferred: this asks frame_authority rather than re-deriving the rule.
        # [[unknown-stays-unknown]] [[label-outlived-referent]]
        _cert, _cert_why = (False, "no seal for this session")
        # ⚠ INITIALISED PER ROW, and that is not a formality. `_verdict` is only assigned
        # inside `if has_seal:`, so leaving it out of this line let a reel with NO seal
        # inherit the previous iteration's verdict. Measured the moment it was wired:
        # 27 rows reported EMPTY when only 22 seals are empty — more EMPTY answers than
        # there are empty seals, which is the arithmetic that exposed it.
        _verdict = None
        if has_seal:
            try:
                # local import: `FA` above lives inside a try, so it is undefined on the path where
                # frame_authority would not load — and a NameError there would read as "not
                # certified" rather than "could not be asked".
                import frame_authority as _FA
                _cert, _cert_why = _FA.seal_covers_extraction(seals.get(sid) or {})
                # ⚠ v2702 — AND SAY WHICH KIND OF "NOT CERTIFIED" THIS IS. The bool above cannot
                # tell an empty examination from an absent one, so 22 of his 30 seals reported as
                # failures when every one of them covers 0 rows and RECORDS that there was nothing
                # to take. `certified` keeps its strict meaning; `sealVerdict` says whether the
                # false is EMPTY (measured, nothing there) or UNEVIDENCED (nobody can tell).
                try:
                    _verdict, _vwhy = _FA.seal_verdict(seals.get(sid) or {})
                except Exception:
                    _verdict, _vwhy = (None, None)
                if _verdict == getattr(_FA, "EMPTY", "EMPTY"):
                    _cert_why = _vwhy
            except Exception as _e:
                _cert, _cert_why = (False, "the contract could not be asked (%s)" % str(_e)[:60])

        if not seals and swhy:
            state, why = UNKNOWN, swhy
        elif has_seal and not names_known:
            # ⚠⚠ v2772 — A DEAD JOURNAL USED TO READ AS A CLEAN CAPTURE FAILURE. `_named_sessions`
            # returns ({}, why) when the ring cannot be resolved, and only the no-rows fallback
            # ever looked at that why — so every sealed reel dropped to `n == 0` and printed
            # "the reader never yielded an item name for this session either. This one IS a
            # capture question", which is REG-340's answer to a question nobody managed to ask.
            # On any venue without his journal (a CI runner, a fresh clone) that is 12 confident
            # capture verdicts built on a file that would not open.
            # [[unknown-stays-unknown]] [[zero-needs-a-denominator]]
            state = UNKNOWN
            why = ("this session IS sealed, but %s — so whether the reader ever got a name for it "
                   "is UNKNOWN. Not zero, and certainly not a capture problem." % nwhy)
        elif has_seal and n and hold is True:
            state = RECOVERABLE
            why = ("SEALED and the reader already read %d item name(s) for this session, %d of "
                   "them with a container OPEN — the names EXIST, a cell box exists for them, and "
                   "the seal carries neither. A join, not a capture problem."
                   % (n, int(_nm.get("panel") or 0)))
        elif has_seal and n:
            # ⚠ NOT folded into NO_NAMES, and the difference is the whole point. NO_NAMES sends
            # the reel to REG-340 ("film the panel"). This reel's reader worked fine; there is
            # simply no holding in what it read, so no footage is owed and no join is either.
            state = NOT_A_HOLDING
            why = ("SEALED, and the reader did read %d item name(s) for this session — but %s "
                   "Nothing is owed here: it is neither a join nor a capture gap." % (n, hwhy))
        elif has_seal:
            state = NO_NAMES
            why = ("sealed, and the reader never yielded an item name for this session either. "
                   "This one IS a capture question: a grid-only reel has no tooltip to read a "
                   "name from. [[REG-340]]")
        elif n:
            state = UNSEALED
            why = ("%d item name(s) were read, but this session has no seal at all, so the "
                   "extraction contract was never even asked about it" % n)
        elif not names_known:
            # unsealed is a fact about the SEAL store and stands on its own; the name count is
            # what went unmeasured, so the sentence may not claim one was never read.
            state = UNSEALED
            why = ("no seal at all, so the extraction contract was never asked about this "
                   "session. Whether any name was read is UNKNOWN — %s" % nwhy)
        else:
            state = UNSEALED
            why = "no seal, and no item name was ever read for this session"

        rows.append({"reel": reel, "session": sid, "state": state, "names": n,
                     "sealed": has_seal, "certified": bool(_cert), "certifiedWhy": _cert_why,
                     # the three-state beside the bool, never instead of it: a reader that
                     # only knows `certified` keeps the strict answer it already had.
                     "sealVerdict": _verdict,
                     "why": why,
                     "scenario": scenario, "scenarioWhy": s_why,
                     # ⚠ True / False / None, and None is a real answer here — see
                     # holding_possible(). A reader that only knows `state` still gets the same
                     # verdict; this is the reason underneath it, carried rather than re-derived.
                     "holdingPossible": hold, "holdingWhy": hwhy,
                     # v2772 — was the NAME COUNT measurable at all on this venue. Without it a
                     # `names: 0` from a journal that would not open is indistinguishable from a
                     # journal that opened and held nothing. [[zero-needs-a-denominator]]
                     "namesKnown": bool(names_known),
                     # ⚠ v2588 — THE CHRONICLE COUNT WAS DROPPED. A cold review noticed the
                     # scenario is an if/elif, so a reel with BOTH panel and chronicle names
                     # reports PANEL — correct, because a slot can exist for the panel ones — and
                     # the chronicle names then had no field at all and became invisible. The
                     # LEAD is still panel; all three counts are carried so nothing vanishes
                     # behind the verdict. [[unknown-stays-unknown]]
                     "panelNames": int(_nm.get("panel") or 0),
                     "floorNames": int(_nm.get("floor") or 0),
                     "chronicleNames": int(_nm.get("chronicle") or 0)})
        counts[state] = counts.get(state, 0) + 1

    rec = counts.get(RECOVERABLE, 0)
    noth = counts.get(NOT_A_HOLDING, 0)
    # ⚠ v2772 — THE RECOVERABLE HEADLINE NEEDS ITS OWN DENOMINATOR. "4 recoverable" was read all
    # session as "4 reels of work owed", and 1 of the 4 held 82% of the names and owed nothing.
    # So the sentence now says how many names sit under each verdict, split the way the contract
    # splits them. [[zero-needs-a-denominator]]
    _rec_names = sum(int(r.get("panelNames") or 0) for r in rows if r["state"] == RECOVERABLE)
    _noth_names = sum(int(r.get("names") or 0) for r in rows if r["state"] == NOT_A_HOLDING)
    return {
        "ok": bool(rows), "rows": rows, "counts": counts, "walked": len(rows),
        "recoverable": rec,
        "notAHolding": noth,
        # the two figures the headline is about, published rather than left to be re-summed
        "recoverablePanelNames": _rec_names,
        "notAHoldingNames": _noth_names,
        "namesKnown": bool(names_known),
        "state": (UNKNOWN if not rows else ("PARTIAL" if counts.get(UNKNOWN) else "MEASURED")),
        "why": (("%d reel(s) measured. %s — **%d carry a RECOVERABLE gap**: sealed, and %d item "
                 "name(s) read WITH A CONTAINER OPEN are already in the journal, so a cell box "
                 "exists for them and the seal carries neither. Those are a JOIN to fix where the "
                 "seal is written, not footage he has to re-film.%s "
                 "⚠ Nothing here writes a seal: back-filling one would forge the certification "
                 "it stands for."
                 % (len(rows), " · ".join("%s %d" % (k, v) for k, v in sorted(counts.items())),
                    rec, _rec_names,
                    ((" %d further reel(s) are sealed with %d name(s) that can never become a "
                      "holding (Chronicle checklist entries, or floor items with no cell) — "
                      "counted apart as NOT_A_HOLDING, because joining those would invent "
                      "possessions rather than recover them." % (noth, _noth_names))
                     if noth else "")))
                if rows else (nwhy or "no reel reached the extract gap reader")),
    }


def main(argv):
    r = gap([a for a in argv if not a.startswith("-")] or None)
    if "--json" in argv:
        print(json.dumps(r, indent=2, sort_keys=True, default=str))
        return 0
    print("\nEXTRACT GAP — why a reel cannot be extracted, and whether that is recoverable\n")
    if not r["ok"]:
        print("  %s\n" % r["why"])
        return 0
    for k, v in sorted(r["counts"].items()):
        print("  %-13s %d" % (k, v))
    print()
    for row in r["rows"][:50]:
        print("  %-34s %-12s names=%-4d %s" % (row["reel"][:34], row["state"], row["names"],
                                               "sealed" if row["sealed"] else "-"))
    print("\n  %s\n" % r["why"])
    return 0


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
