# -*- coding: utf-8 -*-
"""THE RIVER AS FOUR LANES — the shape he asked to SEE, over the nine stations that actually exist.

Konyo: *"the visual rendering of it i want it replicating a simple · INTAKE where the reels come
and get stationed · PRINTER where they get filtered · CAPTURE where they get extracted.. and
finally TOMBSTONE. now obivously the logic behind the backed is not sycned and is not 1000% doing
this.. but the stamps and everything and the movement of them going down that architure and
structure i want built. first in first out FIFO.. that way its optimzed."*

And, decisively: *"now dont get me wrong. the backend should be pinpoint perfect and nothing
fabricated what so ever.. just the visual rendering of the backend and the entire process of the
reel coming in extracted and then out i want that visually built."*

=== ⚠⚠ SO THIS IS A VIEW, NOT A SECOND PIPELINE ===
Nothing here decides where a reel is. `reel_router.route()` decides, and this GROUPS its answer.
The moment this file starts computing a station of its own, the console shows a river the backend
does not have — which is the one thing he ruled out.

=== ⚠⚠ THE LANE MAP IS A PARTITION, AND THAT IS ENFORCED ===
Every station in `reel_router.STATIONS` belongs to EXACTLY ONE lane. Not zero, not two.
`assert_partitions()` proves it against the router's own tuple rather than against a copy, so a
tenth station added upstream turns this RED instead of quietly vanishing from his screen — the
`reel_story` failure this family already lived through, where four of six stages were permanently
empty and nothing said so.

MEASURED on his shelf the day this was written (40 reels):

    INTAKE       7   INTAKE:0 + TRIAGE:0 + STATION:7 + EMPTY:0
    PRINTER     11   PRINTER:11
    CAPTURE     16   CAPTURE:12 + JOIN:4
    TOMBSTONE    6   ROUTED:6 + TOMBSTONE:0
    TOTAL       40   = shelf, reconciles True

⚠ TOMBSTONE READS 6 AND NOT 0 ONLY BECAUSE v2764 UNWELDED ROUTED FROM THE DELETER. Before that,
the last lane could never hold anything: the only writer of a tombstone row lived inside the
deleter, behind the arming lock. The lane would have been a permanently empty box with a label.

=== FIFO IS INHERITED, NEVER RE-SORTED ===
`reel_router.route()` already orders oldest-capture-first and puts reels with NO readable clock
LAST (None must not become 0, which is 1970 and would put every unmeasured reel at the head). A
second sort here would be a second copy of that rule, free to drift. [[copy-drift]]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

#: The four lanes he named, in river order, each over the REAL stations it covers.
#: ⚠ THE STATION NAMES ARE THE ROUTER'S. `assert_partitions()` holds this to `reel_router.STATIONS`.
LANES = (
    ("INTAKE", ("INTAKE", "TRIAGE", "STATION", "EMPTY"),
     "the reels arrive and get stationed — surveyed, or waiting to be"),
    ("PRINTER", ("PRINTER",),
     "names have been read off the frames and the session carries no seal yet"),
    ("CAPTURE", ("CAPTURE", "JOIN"),
     "the names are extracted and joined to a seal"),
    ("TOMBSTONE", ("ROUTED", "TOMBSTONE"),
     "closed out — the extraction contract is satisfied; release is a separate, locked act"),
)


def assert_partitions():
    """Every router station belongs to exactly one lane. -> (ok, findings)

    ⚠⚠ THE FAILURE THIS CATCHES IS SILENT BY NATURE. A station added upstream and not mapped here
    simply stops appearing on his shelf: the lanes still add up among themselves, the page still
    renders, and reels quietly leave the picture. That is `reel_story`'s exact defect — four of six
    stages permanently empty with nothing saying so — and it is why this compares against the
    ROUTER'S tuple instead of a list kept here. [[the-unjoined-end]]
    """
    findings = []
    try:
        import reel_router as _rr
    except Exception as exc:
        return False, ["reel_router could not be imported (%s) — a REFUSAL, never a pass"
                       % type(exc).__name__]
    declared = tuple(getattr(_rr, "STATIONS", ()) or ())
    if not declared:
        return False, ["reel_router.STATIONS is empty, so this guard inspected nothing — an "
                       "instrument failure, not a clean result"]
    seen = {}
    for lane, stations, _why in LANES:
        for st in stations:
            seen.setdefault(st, []).append(lane)
    for st in declared:
        if st not in seen:
            findings.append("station %r is in no lane, so every reel sitting there is INVISIBLE on "
                            "the shelf while the counts still add up among themselves" % st)
        elif len(seen[st]) > 1:
            findings.append("station %r is in %d lanes (%s) — a reel would be counted twice and "
                            "the total would exceed the shelf" % (st, len(seen[st]), seen[st]))
    for st in seen:
        if st not in declared:
            findings.append("lane map names %r, which reel_router does not have — the shelf would "
                            "show a lane the backend cannot fill" % st)
    return (not findings), findings


def lanes(rep=None):
    """The four lanes over the router's answer. Decides nothing. -> dict

    -> {"ok", "lanes": [{name, why, stations, count, reels: [...]}], "shelf", "unknown",
        "reconciles", "why"}

    ⚠ `reconciles` IS PUBLISHED, NOT ASSUMED. It is the sum over lanes plus UNKNOWN against the
    shelf. A view that quietly drops a reel is the whole reason the router returns a report rather
    than a list, and inheriting that discipline is the point.
    """
    out = {"ok": False, "lanes": [], "shelf": 0, "unknown": 0, "reconciles": False, "why": ""}
    if rep is None:
        try:
            import reel_router as _rr
            rep = _rr.route()
        except Exception as exc:
            out["why"] = ("the router could not be walked (%s), so the shelf is UNKNOWN — this is "
                          "NOT an empty river" % type(exc).__name__)
            return out
    if not isinstance(rep, dict) or not rep.get("ok"):
        out["why"] = ("the router did not answer (%s), so there are no lanes to draw and this is "
                      "not a report that the river is empty"
                      % ((rep or {}).get("why") or "no reason given"))
        return out
    ok, findings = assert_partitions()
    if not ok:
        # ⚠ REFUSE TO DRAW A RIVER THAT WOULD LOSE REELS. Rendering four tidy lanes over a broken
        # map is worse than rendering nothing, because it looks complete. [[unknown-stays-unknown]]
        out["why"] = "the lane map does not partition the router's stations: %s" % "; ".join(findings)
        return out
    by = {}
    for r in (rep.get("reels") or []):
        by.setdefault(r.get("station"), []).append(r)
    total = 0
    for name, stations, why in LANES:
        # ⚠ FIFO INHERITED: `rep["reels"]` is already oldest-first, so walking it once per lane
        # preserves that order without re-sorting. Concatenating per station would NOT — it would
        # order by station first and clock second.
        reels = [r for r in (rep.get("reels") or []) if r.get("station") in stations]
        total += len(reels)
        out["lanes"].append({
            "name": name,
            "why": why,
            "stations": list(stations),
            "count": len(reels),
            "byStation": {s: len(by.get(s) or []) for s in stations},
            "reels": reels,
        })
    out["shelf"] = rep.get("shelf") or 0
    out["unknown"] = rep.get("unknown") or 0
    out["reconciles"] = (total + out["unknown"]) == out["shelf"]
    out["ok"] = True
    out["why"] = rep.get("why") or ""
    if not out["reconciles"]:
        out["why"] = ("the lanes hold %d reel(s) and the shelf has %d — %d have gone missing from "
                      "the picture" % (total, out["shelf"], out["shelf"] - total - out["unknown"])) \
                     + ((" · " + out["why"]) if out["why"] else "")
    return out


def main(argv):
    import json
    if "--check" in argv:
        ok, f = assert_partitions()
        print("lane map partitions the router's stations: %s" % ("ok" if ok else "FAILED"))
        for x in f:
            print("  - %s" % x)
        return 0 if ok else 1
    rep = lanes()
    if not rep["ok"]:
        print("UNKNOWN — %s" % rep["why"])
        return 1
    print("THE RIVER, FOUR LANES (shelf %d, reconciles %s)" % (rep["shelf"], rep["reconciles"]))
    for ln in rep["lanes"]:
        bits = " + ".join("%s:%d" % (s, ln["byStation"][s]) for s in ln["stations"])
        print("  %-10s %3d   %s" % (ln["name"], ln["count"], bits))
        if "--reels" in argv:
            for r in ln["reels"][:5]:
                print("        %-34s %s" % (r["reel"][:34], r["station"]))
    if not rep["reconciles"]:
        print("\n⚠ %s" % rep["why"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
