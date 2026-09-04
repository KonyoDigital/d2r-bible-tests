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
                    if names:
                        out[sid] = out.get(sid, 0) + len(names)
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
        n = int(named.get(sid) or 0)
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
                     "sealed": has_seal, "why": why})
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
