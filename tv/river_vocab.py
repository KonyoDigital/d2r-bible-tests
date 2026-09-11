#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🌊 ONE VOCABULARY FOR THE RIVER — position, work, sub-pipeline and progress are FOUR
QUESTIONS, and until v2946 four modules answered them with four lists that looked like rivals.

Konyo, 2026-09-11, shown the four side by side: *"this is a mess.. make it unified and fix whats
needed.."*

⚠⚠ MEASURED BEFORE THIS EXISTED — the mess was not cosmetic:
  reel_router.STATIONS  9  INTAKE..TOMBSTONE   "a reel's station is its POSITION"
  river.STAGES         11  capture..disk       "order matters - it is the river"
  reel_story.STAGES     6  filmed..releasable  "the order a reel moves through"
  printer.STATIONS      7  in..tombstone       the PRINTER's own pipeline
Three claimed to BE the river. Two separately declared a `tombstone`. The journal's stamps used a
9th name, `UNKNOWN`, that no module declared at all.

⚠ THE RESOLUTION IS ALREADY WRITTEN IN reel_router's OWN COMMENT, and it is why nothing here is
renamed: *"A reel's station is its POSITION; what it OWES is the named gate in front of it.
Keeping those separate is the whole point - two reels can sit at the same position and owe
different work, and one word for both is how `route` became the retention tag."*

So: POSITION is reel_router's. `river.STAGES` is the WORK LADDER, never a rival river.
`printer.STATIONS` runs INSIDE the PRINTER station. `reel_story.STAGES` is PROGRESS, a
coarser lifecycle view. Each keeps its list; this module says which question each one answers,
and the gate refuses a fifth list that answers none of them.

⚠ NOT A COPY. STATIONS is IMPORTED from reel_router, never restated — a second copy of the river
is the defect this file exists to end. [[copy-drift]] [[the-unjoined-end]]
"""
import os
import sys

HERE_BOOT = os.path.dirname(os.path.abspath(__file__))
if HERE_BOOT not in sys.path:
    sys.path.insert(0, HERE_BOOT)

# ⚠ v2947 — THIS FILE PRINTS NON-ASCII, SO IT MUST MAKE STDOUT SAFE FIRST.
# The gate caught it: on a non-UTF-8 console (Windows cp1255) a bare print of an emoji CRASHES
# the script, and the crash lands on his cousin's machine, not here. [[windows-powershell-gotchas]]
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import reel_router as _rr   # noqa: E402

#: THE river. Position, in order. Imported, never copied.
STATIONS = tuple(_rr.STATIONS)

#: ⚠ A DECLARED SENTINEL, NOT A STATION. The journal already carried `UNKNOWN` rows before any
#: module admitted the word existed. A position nobody has established is UNKNOWN and must stay
#: sayable — collapsing it into a real station would invent a location. [[unknown-stays-unknown]]
UNPLACED = "UNKNOWN"

#: Every station a stamp may legally carry.
STAMPABLE = STATIONS + (UNPLACED,)

#: The two ends of the river, named so a law can ask whether either has ever been witnessed.
SOURCE, MOUTH = STATIONS[0], STATIONS[-1]

#: WHO ANSWERS WHAT. A module declaring an ordered list about reels must appear here, with the
#: question it answers. Two entries may not share a question.
REGISTRY = {
    "reel_router.STATIONS": "position",
    "river.STAGES":         "work-ladder",
    "printer.STATIONS":     "sub-pipeline:PRINTER",
    "reel_story.STAGES":    "progress",
}


def questions():
    """-> {question: [owner, ...]}  so a caller can see a collision rather than guess."""
    out = {}
    for owner, q in REGISTRY.items():
        out.setdefault(q, []).append(owner)
    return out


def stations_in_journal(path=None):
    """Every station name the journal actually carries. -> (set, why)

    Facts, never a verdict: an empty set means the journal could not be read, and that is
    returned as a `why` rather than as a clean-looking zero. [[zero-needs-a-denominator]]
    """
    import json
    p = path or os.path.join(HERE, "river_stamp.jsonl")
    if not os.path.exists(p):
        return set(), "no journal at %s" % os.path.basename(p)
    seen, n = set(), 0
    try:
        # ⚠ v2947 — this read `io.open(...) if False else open(...)`, and `io` is not imported
        # here. The dead branch never ran, so nothing failed — until the gate that walks every call
        # for a name nothing binds found it. A leftover is still an unbound name.
        for ln in open(p, encoding="utf-8"):
            ln = ln.strip()
            if not ln:
                continue
            try:
                r = json.loads(ln)
            except Exception:
                continue
            n += 1
            if r.get("station"):
                seen.add(str(r["station"]))
    except Exception as e:
        return set(), "journal unreadable: %s" % str(e)[:60]
    return seen, ("" if n else "journal has no rows")


def undeclared(path=None):
    """Stations the journal uses that no module declares. -> (sorted list, why)"""
    seen, why = stations_in_journal(path)
    return sorted(seen - set(STAMPABLE)), why


def health(path=None):
    """WHAT THE RIVER CAN AND CANNOT SAY ABOUT ITS OWN MOVEMENT. -> dict

    ⚠⚠ EVERY FIELD CARRIES ITS DENOMINATOR, because the first three answers this file produced
    were all artifacts that looked like measurements:
      · `STATION -> CAPTURE  median 3.2 days` was the age of a BACKFILL, not a dwell. 40 of 122
        rows were written by `claude:first-wiring` in one batch, 37 of them inside four
        consecutive milliseconds.
      · 96 of 122 rows are `byKind: observer` — "I noticed it here", which cannot time a move.
      · actor->actor transitions: 0. Twenty actor rows exist, but no reel has TWO, so not one
        dwell in this river is measurable. `dwellMeasurable` is therefore False and `dwellS` is
        None — never 0, which would read as "instant". [[zero-needs-a-denominator]]
    [[unknown-stays-unknown]] [[stale-reading]]
    """
    import json
    p = path or os.path.join(HERE, "river_stamp.jsonl")
    out = {"rows": 0, "reels": 0, "byKind": {}, "backfilled": 0, "standing": {},
           "actorTransitions": 0, "dwellMeasurable": False, "dwellS": None,
           "undeclared": [], "endsWitnessed": {}, "why": ""}
    if not os.path.exists(p):
        out["why"] = "no journal at %s" % os.path.basename(p)
        return out
    rows = []
    try:
        with open(p, encoding="utf-8") as fh:
            for ln in fh:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    rows.append(json.loads(ln))
                except Exception:
                    pass
    except Exception as e:
        out["why"] = "journal unreadable: %s" % str(e)[:60]
        return out
    out["rows"] = len(rows)
    per = {}
    for r in rows:
        k = str(r.get("byKind"))
        out["byKind"][k] = out["byKind"].get(k, 0) + 1
        if r.get("by") == "claude:first-wiring":
            out["backfilled"] += 1
        if r.get("reel"):
            per.setdefault(r["reel"], []).append(r)
    out["reels"] = len(per)
    for reel, rs in per.items():
        rs.sort(key=lambda x: x.get("seq") or 0)
        st = rs[-1].get("station")
        out["standing"][st] = out["standing"].get(st, 0) + 1
        acts = [x for x in rs if x.get("byKind") == "actor"]
        out["actorTransitions"] += max(0, len(acts) - 1)
    out["dwellMeasurable"] = out["actorTransitions"] > 0
    seen = {str(r["station"]) for r in rows if r.get("station")}
    out["undeclared"] = sorted(seen - set(STAMPABLE))
    out["endsWitnessed"] = {SOURCE: SOURCE in seen, MOUTH: MOUTH in seen}
    # ⚠⚠ THE MOUTH IS READ FROM THE LEDGER, NOT FROM A STAMP — AND I GOT THIS WRONG FIRST.
    # A tombstoned reel LEAVES THE DISK: it stops being a card and becomes a row in
    # reel_tombstones.json. So "gone from disk and never stamped TOMBSTONE" is NOT a hole, it is
    # the normal exit, and `control_app.river_mouth()` already reads the terminus from the ledger
    # on purpose — putting it in the router would push a retention fact inside
    # assert_independent_of_retention(), the one thing that guard exists to prevent.
    # MEASURED 2026-09-11: 36 river-tracked reels gone from disk, and ALL 36 are in the ledger.
    # goneWithoutTombstone = 0. The 446 ledger rows are reels that finished.
    # ⚠ My first reading said "36 left through a hole" because it looked for a river STAMP rather
    # than a ledger ROW. control_app.river_mouth's own docstring had already ruled on this
    # ("WHY TOMBSTONE LOOKED UNREACHABLE, AND WHY THAT READING WAS WRONG") and I had not read it.
    # [[carved-skill-unloaded-is-unapplied]] [[inherited-claim-is-not-evidence]]
    hist = os.path.join(HERE, "frames", "hist")
    out["atMouth"] = None
    try:
        import reel_retention as _rr
        import json as _json
        _tp = _rr._tombstone_path()
        with open(_tp, encoding="utf-8") as _fh:
            _doc = _json.load(_fh) or {}
        _tomb = {str(r.get("reel") or r.get("name") or r.get("id"))
                 for r in (_doc.get("reels") or []) if isinstance(r, dict)}
        out["atMouth"] = len(_tomb)
    except Exception:
        _tomb = None                  # None = the ledger could not be asked, never "nobody finished"
    if os.path.isdir(hist):
        try:
            _disk = set(os.listdir(hist))
            _gone = set(per) - _disk
            out["onDisk"] = len([d for d in _disk if d.startswith("reel_")])
            out["goneFromDisk"] = len(_gone)
            out["goneWithoutTombstone"] = None if _tomb is None else len(_gone - _tomb)
        except Exception as e:
            out["onDisk"] = None
            out["why"] = (out["why"] + " | store unreadable: %s" % str(e)[:50]).strip(" |")
    else:
        out["onDisk"] = None          # None = nobody looked, never 0
    if not out["dwellMeasurable"]:
        out["why"] = ("no reel carries two ACTOR stamps, so no dwell in this river is measurable: "
                      "%d row(s) over %d reel(s), %d backfilled, %s"
                      % (out["rows"], out["reels"], out["backfilled"],
                         " ".join("%s=%d" % kv for kv in sorted(out["byKind"].items()))))
    return out


if __name__ == "__main__":
    print("  STATIONS (%d): %s" % (len(STATIONS), " -> ".join(STATIONS)))
    print("  sentinel: %s     source=%s  mouth=%s" % (UNPLACED, SOURCE, MOUTH))
    for q, owners in sorted(questions().items()):
        print("  %-22s %s" % (q, ", ".join(owners)))
    seen, why = stations_in_journal()
    print("  journal uses %d name(s)%s" % (len(seen), (" (%s)" % why) if why else ""))
    bad, _ = undeclared()
    print("  undeclared: %s" % (", ".join(bad) or "none"))
    for end in (SOURCE, MOUTH):
        print("  %-9s witnessed in journal: %s" % (end, end in seen))
