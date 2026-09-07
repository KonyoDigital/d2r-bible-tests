# -*- coding: utf-8 -*-
"""THE RIVER'S OUTLET — the lane that closes a reel out WITHOUT deleting it.

Konyo's architecture, in his words: *"it just flows and eats session reels regardless of the route
it come from initially… it just gets spit out properly and indicually related to each cell"*, and
*"there is no loop or worry because it gets eventually tombstoned and deleted and wiped completely.
only the data and information gets extracted before hand."*

=== ⚠⚠ THE WELD THIS UNDOES ===
`river_walk.py` recorded the gap in its own note for ROUTED:

    "the gate is TOMBSTONE, and the ONLY writer of a tombstone row runs inside the deleter
     (`reel_retention.apply_plan` -> `_tombstone`). So a reel cannot be recorded as closed out
     without being removed, and removal is behind the arming lock. That weld is the gap this
     station has been empty for"

So *being finished* and *being deleted* were the same event, and the deleter is behind
`_PRUNE_SAFE_TO_RUN`, which is False and STAYS FALSE. A river whose only exit is a locked door has
no outlet at all: measured on his shelf, 40 reels, ROUTED 0 and TOMBSTONE 0, and `route()` already
published `unreached: [INTAKE, TRIAGE, ROUTED, TOMBSTONE]` rather than letting the zeros read as
"none waiting".

**ROUTED and TOMBSTONE are two different facts.** ROUTED is what `reel_router.OWES` already says it
is — *"the extraction contract is satisfied; it may be released with a stamp"* — a statement about
the DATA. TOMBSTONE is a statement about the BYTES. This lane writes the first and never the
second, so a reel can finish the river while its footage stays exactly where it is.

=== WHICH REELS THIS ROUTES, AND WHY IT REFUSES THE OTHERS ===
The station table is the authority; this lane invents nothing. `reel_router.OWES` says:

    EMPTY    "ROUTE — …⚠⚠ THAT IS NOT AN EXIT… it continues down the same river carrying less"
    CAPTURE  "CAPTURE, then ROUTE — …it still owes a route and a stamped tombstone"

Measured on his shelf: EMPTY 6, CAPTURE 12.

  ROUTES  **EMPTY only.** retro_triage walked the reel IN FULL and found ZERO panel frames. There
          is no name, no location and no provenance to extract, so the extraction contract is
          satisfied VACUOUSLY — and that is a real way to satisfy it, not a dodge.

  REFUSES **CAPTURE**, all 12, and says why. Its own OWES puts a step in front of the route
          ("CAPTURE, then ROUTE"), and no stamp can supply a capture. Routing them would claim an
          extraction contract that was never satisfied for a name the reel demonstrably holds
          (REG-340: D2R prints it on the character panel, which the reel does not film). ⚠ THE
          REFUSAL IS PUBLISHED, NOT SILENT — 12 reels that owe a route and cannot take one are a
          finding, and a lane that quietly skipped them would report "6 routed" and read as done.

=== ⚠⚠ WHY THIS CANNOT FLAP ===
`reel_router._station_of` derives a station from EVIDENCE, and routing does not change any
evidence — so the next walk would derive EMPTY again, the observer walk would stamp EMPTY, and the
reel would oscillate ROUTED→EMPTY→ROUTED for ever, writing a transition row each time.

The outlet overlay in `reel_router.route()` reads **actor rows only**. An actor row is written by a
lane that acted; the observer walk cannot write one (`river_stamp.run()` hard-codes
`byKind: "observer"` with no option to say otherwise). So the overlay is driven purely by acts,
never by its own output, and a routed reel simply stays routed.

[[the-unjoined-end]] [[unknown-stays-unknown]]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

# ⚠ WINDOWS PRINTS THIS FILE'S OWN REPORT IN cp1255, AND THE ARROWS AND WARNING SIGNS IN
# every `why` string below would crash the CLI WHILE IT REPORTS — a clean run exiting
# non-zero on the machine that cannot run the suite. [[windows-powershell-gotchas]]
try:
    from console_safe import enable
    enable()
except Exception:
    pass

#: The station this lane moves reels TO.
STATION = "ROUTED"

#: Stations whose OWES names a route with NOTHING in front of it.
#: ⚠ A station is in here because `reel_router.OWES[st]` says so, not because this file thinks it
#: should be. If that table changes, `assert_matches_owes()` goes red rather than this drifting.
ROUTES_FROM = ("EMPTY",)

#: Stations that owe a route with a step IN FRONT of it. Refused, loudly, with the step named.
BLOCKED_BY = {
    "CAPTURE": "a capture change — REG-340: the item name is printed on the character panel, "
               "which the reel does not film. No stamp can supply that, and no reading lane can "
               "either, so this reel owes a CAPTURE before it can owe a route",
}


def _why_for(station, reel_why):
    """The sentence that goes in the stamp. -> str

    ⚠ IT CARRIES THE REEL'S OWN REASON, not a lane slogan. Six identical rows saying "routed" would
    make the store unreadable a month from now; the row has to say what was true about THIS reel.
    """
    if station == "EMPTY":
        return ("nothing to extract and the survey proved it — retro_triage walked this reel IN "
                "FULL and found zero panel frames, so the extraction contract (name, location, "
                "provenance) is satisfied vacuously. It owes only a tombstone. [%s]" % reel_why)
    return "routed from %s — %s" % (station, reel_why)


def plan(rep=None):
    """Who would be routed, who would be refused, and why. Writes NOTHING. -> dict

    -> {"ok", "route": [...], "declined": [...], "shelf", "why"}
    ⚠ `declined` IS NOT AN ERROR LIST. It is the part of the shelf that owes a route and cannot
    take one yet, which is the honest other half of any number this lane reports.
    """
    out = {"ok": False, "route": [], "declined": [], "shelf": 0, "why": ""}
    if rep is None:
        try:
            import reel_router as _rr
            rep = _rr.route()
        except Exception as exc:
            out["why"] = ("the router could not be walked (%s), so nothing is known about the "
                          "shelf — that is a REFUSAL, not an empty queue" % type(exc).__name__)
            return out
    if not isinstance(rep, dict) or not rep.get("ok"):
        out["why"] = ("the router did not answer (%s), so this lane has no shelf to act on and is "
                      "NOT reporting that nothing needs routing"
                      % ((rep or {}).get("why") or "no reason given"))
        return out
    # ⚠ FIFO, and it is INHERITED rather than re-sorted. `reel_router.route()` already orders
    # oldest-capture-first and puts reels with NO readable clock last — re-sorting here would be a
    # second copy of that rule, free to drift from it. [[copy-drift]]
    for r in (rep.get("reels") or []):
        st = r.get("station")
        if st in ROUTES_FROM:
            out["route"].append({"reel": r.get("reel"), "from": st,
                                 "capturedMs": r.get("capturedMs"),
                                 "why": _why_for(st, r.get("why") or "")})
        elif st in BLOCKED_BY:
            out["declined"].append({"reel": r.get("reel"), "from": st,
                                    "owesFirst": BLOCKED_BY[st]})
    out["ok"] = True
    out["shelf"] = rep.get("shelf") or 0
    out["why"] = ("%d reel(s) can be routed now; %d owe a step first"
                  % (len(out["route"]), len(out["declined"])))
    return out


def apply(by, rep=None, limit=None, path=None):
    """Stamp each routable reel ROUTED, as an ACTOR. -> dict

    ⚠ `by` IS REQUIRED, exactly as `river_stamp.run()` requires it — a row that cannot say what
    moved the reel does not carry the fact it exists to carry.

    ⚠⚠ `observed=False` IS THE WHOLE POINT. This lane ACTED: it decided the contract was satisfied
    and closed the reel out. That is a causal claim it is entitled to make, and it is the only kind
    of row `reel_router`'s outlet overlay will read. An observer row here would be invisible to the
    overlay AND would put an unmeasured cause in an append-only store.
    """
    out = {"ok": False, "routed": 0, "already": 0, "refused": 0, "declined": 0,
           "transitions": [], "refusals": [], "by": str(by or "").strip(), "why": ""}
    if not out["by"]:
        out["why"] = ("apply() needs a `by` — the lane that stamps must name itself or the rows it "
                      "writes cannot say what moved anything")
        return out
    p = plan(rep)
    if not p["ok"]:
        out["why"] = p["why"]
        return out
    out["declined"] = len(p["declined"])
    try:
        import river_stamp as _st
    except Exception as exc:
        out["why"] = "river_stamp could not be imported (%s)" % type(exc).__name__
        return out
    todo = p["route"] if limit is None else p["route"][:max(0, int(limit))]
    for item in todo:
        r = _st.stamp(item["reel"], STATION, by=out["by"], why=item["why"],
                      observed=False, path=path)
        if not r.get("ok"):
            out["refused"] += 1
            out["refusals"].append({"reel": item["reel"], "why": r.get("why")})
        elif r.get("wrote"):
            out["routed"] += 1
            out["transitions"].append({"reel": item["reel"], "from": r.get("from"),
                                       "to": STATION})
        else:
            # ⚠ NOT AN ERROR AND NOT AN EVENT. It was already routed. Counted separately so a
            # second run reports "0 routed, 6 already" and never "0 routed" alone, which would
            # read as a broken lane. [[zero-needs-a-denominator]]
            out["already"] += 1
    out["ok"] = True
    out["why"] = ("%d routed, %d already there, %d refused, %d declined (owe a step first)"
                  % (out["routed"], out["already"], out["refused"], out["declined"]))
    return out


def assert_matches_owes():
    """Prove this lane's station table still agrees with the router's. -> (ok, findings)

    ⚠⚠ THE DRIFT THIS CATCHES. `ROUTES_FROM` and `BLOCKED_BY` are a SECOND statement of something
    `reel_router.OWES` already says. Two copies of one rule is how a lane keeps routing a station
    that stopped owing a route — the fix would land in one table and the lane would go on acting on
    the other, with every gate green. So the copy is checked against the original rather than
    trusted. [[copy-drift]]
    """
    findings = []
    try:
        import reel_router as _rr
    except Exception as exc:
        return False, ["reel_router could not be imported (%s) — that is a REFUSAL, never a pass"
                       % type(exc).__name__]
    owes = getattr(_rr, "OWES", None)
    if not isinstance(owes, dict) or not owes:
        return False, ["reel_router.OWES is missing or empty, so this guard inspected nothing "
                       "— an instrument failure, not a clean result"]
    for st in ROUTES_FROM:
        text = str(owes.get(st) or "")
        if not text:
            findings.append("%r is not a station in reel_router.OWES, so this lane routes from a "
                            "station the router does not have" % st)
        elif not text.strip().upper().startswith("ROUTE"):
            findings.append("this lane routes %r directly, but its OWES now begins %r — the "
                            "station owes something else first and must not be routed"
                            % (st, text[:40]))
    for st in BLOCKED_BY:
        text = str(owes.get(st) or "")
        if not text:
            findings.append("%r is not a station in reel_router.OWES" % st)
        elif "ROUTE" not in text.upper():
            findings.append("this lane refuses %r as owing-a-route-later, but its OWES no longer "
                            "mentions a route at all: %r" % (st, text[:60]))
    # ⚠ THE STATION THIS LANE MUST NEVER WRITE. TOMBSTONE is behind the arming lock and this lane
    # is not the deleter. Pinned as a law so a later edit cannot quietly widen the lane's reach.
    if STATION != "ROUTED":
        findings.append("this lane's STATION is %r. It writes the DATA fact, never the BYTES fact "
                        "— TOMBSTONE belongs to the deleter, behind the arming lock" % STATION)
    return (not findings), findings


def main(argv):
    import json
    by = None
    do = False
    lim = None
    for i, a in enumerate(argv):
        if a == "--by" and i + 1 < len(argv):
            by = argv[i + 1]
        elif a == "--apply":
            do = True
        elif a == "--limit" and i + 1 < len(argv):
            lim = int(argv[i + 1])
        elif a == "--check":
            ok, f = assert_matches_owes()
            print("owes agreement: %s" % ("ok" if ok else "FAILED"))
            for x in f:
                print("  - %s" % x)
            return 0 if ok else 1
    if not do:
        p = plan()
        print(json.dumps(p, indent=1)[:4000])
        print("\n(dry run — pass --apply --by <name> to stamp)")
        return 0 if p["ok"] else 1
    if not by:
        print("--apply needs --by <name>")
        return 2
    r = apply(by)
    print(json.dumps(r, indent=1)[:4000])
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
