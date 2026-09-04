#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""THE 3D/4D PRINTER — every reel in at ONE door, down ONE stream, out the other end.

His words, 2026-09-04: *"3d 4d printer connected to the heart of the console and the reels like we
said going in unified and getting processed and routed out clean on the other end of the stream"*,
and earlier: *"the same feeding system and same routing system working and funneling starting from
the same start point and slowly down the river changing routes individually and accordingly
relevant to that specific routed reel… every single reel goes through the printer and comes out
clean on the other end"*.

⚠⚠ THIS BUILDS NOTHING NEW AND THAT IS THE POINT. Seven modules already answer one question each,
and every one of them was measured on his own forty reels:

    one_start_point   which door a reel entered by            ONE_DOOR      (40 of 40)
    one_funnel        one stage ladder, and its passage       ONE_LADDER · PARTIAL (2 of 6 dated)
    reel_river        the stage reached, decider and question 40 reels, 0 gaps
    per_reel_routes   what decided its route                  UNEXERCISED   (28 content / 12 policy)
    printer_reach     what the printer may act on at all      UNREACHABLE   (0 of 30 seals)
    declared_vs_content  content routing, not a stamp         UNTESTABLE    (1 declaring reel)
    store_owners      one declared owner per store            4 stores

What did NOT exist is the thing he keeps asking for: **ONE surface where a single reel is followed
from the door to the far end**, so *"is the stream working"* is a question anybody can answer by
looking instead of by running seven probes and holding the answers in their head. Every station
below QUOTES its owner. Nothing here re-derives a number, because two derivations of one truth is
how a badge and a diagram come to disagree on screen. [[copy-drift]] §1

⚠⚠ AND IT PRINTS NOTHING AND DELETES NOTHING. The prune stays OFF. This is a REPORT: it routes a
reel on paper and says where it came out. No station may refuse, block, or remove anything.

⚠⚠ THE FAR END IS DELIBERATELY UNDECIDED, AND THAT IS NOT A GAP IN THIS FILE. A15's last clause
says *clean is a state the pipeline must be able to ASSERT per reel* and never says WHICH DOOR
decides. Measured on his shelf the two candidates disagree — 12 of 40 finished by the REEL door, 0
of 15 asked by the FRAME contract — and conjoining them is exactly the collapse v2312 attempted and
WITHDREW, because it would have stopped the prune firing on every reel he owns (v2314: they answer
different questions at different granularities). So the OUT station reports BOTH and marks the reel
UNDECIDED. Choosing is a decision about what *finished* means, it is his, and it gates the prune.
[[unknown-stays-unknown]]

    python3 tv/printer.py                  # every reel, one line each
    python3 tv/printer.py <reel>           # one fish, every station
    python3 tv/printer.py --json
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

#: The stream, in order, and WHO ANSWERS EACH STATION. The module named owns that question; this
#: file owns none of them. A station whose owner will not answer is UNKNOWN, never skipped — a
#: station missing from a reel's row would read as a reel that did not need it.
STATIONS = ("in", "funnel", "route", "extract", "out")

STATION_OWNER = {
    "in":      ("one_start_point",  "which door did this reel enter by?"),
    "funnel":  ("reel_river",       "how far down the one ladder has it come, and who decided?"),
    "route":   ("per_reel_routes",  "what chose its route — its CONTENT, or policy?"),
    "extract": ("printer_reach",    "may the printer act on it at all?"),
    "out":     ("reel_river",       "is it clean at the far end? (BOTH doors, neither chosen)"),
}


def _safe(fn, *a, **k):
    """Call an owner. -> (value, why). An owner that raises is UNKNOWN with its reason."""
    try:
        return fn(*a, **k), ""
    except Exception as e:
        return None, "%s would not answer (%s)" % (getattr(fn, "__name__", "?"), str(e)[:80])


def _sources():
    """Every owner's reading, taken ONCE. -> (dict, list-of-why)

    ⚠ Taken once and shared, so two stations on the same row cannot disagree about the same reel
    because they asked at different moments.
    """
    out, whys = {}, []
    try:
        import one_start_point as OSP
        out["door"], w = _safe(OSP.start_points)
        if w:
            whys.append(w)
    except Exception as e:
        whys.append("one_start_point would not import (%s)" % str(e)[:60])
    try:
        import reel_river as RR
        out["river"], w = _safe(RR.river)
        if w:
            whys.append(w)
    except Exception as e:
        whys.append("reel_river would not import (%s)" % str(e)[:60])
    try:
        import per_reel_routes as PRR
        out["routes"], w = _safe(PRR.routes)
        if w:
            whys.append(w)
    except Exception as e:
        whys.append("per_reel_routes would not import (%s)" % str(e)[:60])
    try:
        import printer_reach as PR
        out["reach"], w = _safe(PR.report)
        if w:
            whys.append(w)
    except Exception as e:
        whys.append("printer_reach would not import (%s)" % str(e)[:60])
    return out, whys


def _by_reel(blob, key="rows"):
    rows = (blob or {}).get(key) or []
    return {str(r.get("reel") or ""): r for r in rows if isinstance(r, dict)}


def stream(reel=None):
    """Follow every reel from the door to the far end. -> dict

    Each row carries one entry per station: what happened, who said so, and the question that
    owner was answering. `out` is never a verdict — see the module docstring.
    """
    src, whys = _sources()
    river = _by_reel(src.get("river"))
    doors = _by_reel(src.get("door"))
    routes = _by_reel(src.get("routes"))
    if not river and not doors:
        return {"ok": False, "state": "UNKNOWN", "rows": [], "counts": {},
                "why": ("UNKNOWN, not an empty shelf — %s"
                        % ("; ".join(whys) if whys else
                           "no owner answered and none said why"))}

    reach = src.get("reach") or {}
    reach_state = reach.get("state") or "UNKNOWN"
    names = sorted(set(river) | set(doors) | set(routes))
    rows, counts = [], {}
    for name in names:
        if reel and reel not in name:
            continue
        rv, dr, rt = river.get(name), doors.get(name), routes.get(name)
        stations = {}

        stations["in"] = ({"say": dr.get("door"), "why": dr.get("why")} if dr else
                          {"say": "UNKNOWN", "why": "one_start_point did not report this reel"})

        stations["funnel"] = ({"say": rv.get("stage"), "why": rv.get("question"),
                               "decider": rv.get("decider")} if rv else
                              {"say": "UNKNOWN", "why": "reel_river did not report this reel"})

        stations["route"] = ({"say": rt.get("decidedBy"), "why": rt.get("why"),
                              "route": rt.get("route")} if rt else
                             {"say": "UNKNOWN", "why": "per_reel_routes did not report this reel"})

        # ⚠ THE REACH IS A SHELF-WIDE FACT, NOT A PER-REEL ONE, and saying otherwise would invent a
        # per-reel measurement nobody took. printer_reach measured that ZERO of 30 seals satisfy
        # the extraction contract, so the disposable path is structurally unreachable for every
        # reel — that is one answer about the whole shelf, printed on each row as what it is.
        stations["extract"] = {"say": reach_state,
                               "why": ("a SHELF-WIDE state, not a per-reel one: %s"
                                       % str(reach.get("why") or "")[:150])}

        # ⚠⚠ BOTH DOORS, NEITHER CHOSEN. See the module docstring.
        if rv is None:
            stations["out"] = {"say": "UNKNOWN", "reelDoor": None, "frameDoor": None,
                               "why": "reel_river did not report this reel, so neither door was asked"}
        else:
            reel_door = bool(rv.get("reelAnswer"))
            frame_door = rv.get("frameAnswer")     # True / False / None(UNASKED)
            stations["out"] = {
                "say": "UNDECIDED",
                "reelDoor": reel_door,
                "frameDoor": frame_door,
                "why": ("the REEL door says %s; the FRAME door says %s. A15 does not say which "
                        "decides, and they answer DIFFERENT questions at different granularities "
                        "(v2314) — conjoining them is the collapse v2312 withdrew. Reported, not "
                        "chosen."
                        % ("yes" if reel_door else "no",
                           {True: "yes", False: "no", None: "UNASKED"}[frame_door])),
            }

        for st in STATIONS:
            counts.setdefault(st, {})
            k = str(stations[st].get("say"))
            counts[st][k] = counts[st].get(k, 0) + 1
        rows.append({"reel": name, "stations": stations})

    unknown = sum(1 for r in rows
                  if any(str(r["stations"][s].get("say")) == "UNKNOWN" for s in STATIONS))
    state = "UNKNOWN" if not rows else ("FLOWING" if not unknown else "PARTIAL")
    return {
        "ok": bool(rows), "state": state, "rows": rows, "counts": counts,
        "walked": len(rows), "unknownStations": unknown,
        "stations": list(STATIONS), "owners": {k: v[0] for k, v in STATION_OWNER.items()},
        "questions": {k: v[1] for k, v in STATION_OWNER.items()},
        "why": (("%d reel(s) followed from the door to the far end across %d station(s). %s "
                 "⚠ THE FAR END IS UNDECIDED FOR EVERY REEL BY DESIGN: A15 never says which door "
                 "decides `clean`, the two candidates disagree on this shelf, and conjoining them "
                 "is the collapse v2312 withdrew. That choice is yours and it gates the prune."
                 % (len(rows), len(STATIONS),
                    ("Every station answered." if not unknown else
                     "%d reel(s) have a station nobody answered." % unknown)))
                if rows else "no reel reached the printer"),
    }


def main(argv):
    reel = next((a for a in argv if not a.startswith("-")), None)
    r = stream(reel)
    if "--json" in argv:
        print(json.dumps(r, indent=2, sort_keys=True, default=str))
        return 0
    print("\nTHE PRINTER — in at one door, down one stream, out the other end\n")
    if not r["ok"]:
        print("  %s\n" % r["why"])
        return 0
    print("  %s · %d reel(s)\n" % (r["state"], r["walked"]))
    for st in STATIONS:
        owner, q = STATION_OWNER[st]
        tally = " · ".join("%s %d" % (k, v) for k, v in sorted(r["counts"].get(st, {}).items()))
        print("  %-8s %-18s %s" % (st.upper(), owner, tally))
        print("           %s" % q)
    if reel:
        print()
        for row in r["rows"]:
            print("  %s" % row["reel"])
            for st in STATIONS:
                s = row["stations"][st]
                print("     %-8s %-12s %s" % (st, s.get("say"), str(s.get("why") or "")[:110]))
    print("\n  %s\n" % r["why"])
    return 0


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
