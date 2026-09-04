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
                    cur = out.get(sid) or {"names": 0, "panel": 0, "floor": 0, "chronicle": 0}
                    cur["names"] += len(names)
                    sc = str(r.get("scene") or "").strip().lower()
                    if sc in PANEL_SCENES:
                        cur["panel"] += len(names)
                    elif sc == "chronicle":
                        cur["chronicle"] += len(names)
                    elif sc in FLOOR_SCENES:
                        cur["floor"] += len(names)
                    out[sid] = cur
        except Exception:
            continue
    return out, ""


def gap(reels=None):
    """Per reel: can it be extracted, and if not, is the gap RECOVERABLE? -> dict"""
    try:
        import reel_river as RR
        riv = RR.river()
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
        if _nm.get("panel"):
            scenario, s_why = "PANEL", ("%d name(s) read with a container OPEN — a slot identity "
                                        "can exist for these" % _nm["panel"])
        elif _nm.get("floor"):
            scenario, s_why = "FLOOR", ("%d name(s) read with NO container open — an item on the "
                                        "ground has no cell, so a slot cannot be asked for"
                                        % _nm["floor"])
        elif _nm.get("chronicle"):
            scenario, s_why = "CHRONICLE", ("%d name(s) read on a Chronicle page — a checklist of "
                                            "items he mostly does not own, never a holding"
                                            % _nm["chronicle"])
        else:
            scenario, s_why = "UNKNOWN", "no name was read for this reel, so no scenario applies"
        has_seal = sid in seals

        if not seals and swhy:
            state, why = UNKNOWN, swhy
        elif has_seal and n:
            state = RECOVERABLE
            why = ("SEALED and the reader already read %d item name(s) for this session — the "
                   "names EXIST and the seal does not carry them. A join, not a capture "
                   "problem." % n)
        elif has_seal:
            state = NO_NAMES
            why = ("sealed, and the reader never yielded an item name for this session either. "
                   "This one IS a capture question: a grid-only reel has no tooltip to read a "
                   "name from. [[REG-340]]")
        elif n:
            state = UNSEALED
            why = ("%d item name(s) were read, but this session has no seal at all, so the "
                   "extraction contract was never even asked about it" % n)
        else:
            state = UNSEALED
            why = "no seal, and no item name was ever read for this session"

        rows.append({"reel": reel, "session": sid, "state": state, "names": n,
                     "sealed": has_seal, "why": why,
                     "scenario": scenario, "scenarioWhy": s_why,
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
    return {
        "ok": bool(rows), "rows": rows, "counts": counts, "walked": len(rows),
        "recoverable": rec,
        "state": (UNKNOWN if not rows else ("PARTIAL" if counts.get(UNKNOWN) else "MEASURED")),
        "why": (("%d reel(s) measured. %s — **%d carry a RECOVERABLE gap**: sealed, and the "
                 "item names the contract wants were already read into the journal. Those are a "
                 "JOIN to fix where the seal is written, not footage he has to re-film. "
                 "⚠ Nothing here writes a seal: back-filling one would forge the certification "
                 "it stands for."
                 % (len(rows), " · ".join("%s %d" % (k, v) for k, v in sorted(counts.items())),
                    rec))
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
