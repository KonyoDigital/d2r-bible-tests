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

  ROUTES  **EMPTY**, and a reel at **JOIN** whose own engine said NOT_A_HOLDING.
          EMPTY: retro_triage walked the reel IN FULL and found ZERO panel frames. There is no
          name, no location and no provenance to extract, so the extraction contract is satisfied
          VACUOUSLY — and that is a real way to satisfy it, not a dodge.
          JOIN + NOT_A_HOLDING: the names were read, and extract_gap ruled that none of them can
          become a holding. No join is owed and no footage is owed. That is the same shape as
          EMPTY — the contract is satisfied, and the reel owes a tombstone. A JOIN reel whose
          verdict is missing, or is anything else (RECOVERABLE included), is not this lane's.
          Unknown is not nothing, and a recoverable join is still owed.

  REFUSES **CAPTURE**, and says why. Its OWES puts hover coverage in front of the route. An
          item's name is in the tooltip; the character panel answers a different question and
          carries no items. Routing a CAPTURE reel would claim a contract the reel did not
          satisfy. ⚠ THE REFUSAL IS PUBLISHED, NOT SILENT — reels that owe a route and cannot
          take one are a finding, and a lane that quietly skipped them would report a count and
          read as done.

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


def _nothing_owed_say():
    """extract_gap's own token for a join that is not a join. -> str | None

    None means the engine could not be asked. That is not a verdict, and it must not route.
    """
    try:
        import extract_gap as _eg
        tok = getattr(_eg, "NOT_A_HOLDING", None)
    except Exception:
        return None
    if isinstance(tok, str) and tok:
        return tok
    return None


def _engine_token(name):
    """extract_gap's own token `name` (JOINED, RECOVERABLE). -> str | None - None when the engine cannot be asked."""
    try:
        import extract_gap as _eg
        tok = getattr(_eg, name, None)
    except Exception:
        return None
    return tok if isinstance(tok, str) and tok else None


def spent_past_window(reels, spent, pinned, shield=None):
    """REG-2004 - the reel ids whose one join re-read is SPENT and that sit OUTSIDE the newest-16 shield. -> set

    His ruling 2026-10-02: every reel but the newest 16 (and the suite's fixtures) is extracted, tallied and then
    tombstoned FIFO - "no station may hold a reel for ever", JOIN included - and a re-read is allowed when extraction
    needs one. #152 slice 4 gave a RECOVERABLE join that one re-read; MEASURED on his Mac 2026-10-07, 7 of them had it
    (0.5-21 h earlier), the seal still recorded an empty examination, and nothing could ever move them again. Inside
    the shield a reel keeps waiting. `spent` or `pinned` None (unreadable / still scanning) = nothing, fail closed.
    `shield` is the CALLER's newest-16 function (reel_retention.recent_shield): this lane never imports the deleter's
    module (test_the_river_has_an_outlet), and no function handed in means nothing routes."""
    if spent is None or pinned is None or not callable(shield):
        return set()
    try:
        shield = set(shield(list(reels)))
    except Exception:
        return set()
    pin = set(str(x) for x in pinned)
    return set(str(r) for r in reels if r in spent and r not in shield and str(r) not in pin)


def _why_for(station, reel_why, ruled=None):
    """The sentence that goes in the stamp. -> str

    ⚠ IT CARRIES THE REEL'S OWN REASON, not a lane slogan. Six identical rows saying "routed" would
    make the store unreadable a month from now; the row has to say what was true about THIS reel.
    `ruled` is the engine's own token, when this reel was routed because that token said nothing
    is owed. The sentence cites that token. It does not invent a second one.
    """
    if ruled and ruled == _engine_token("JOINED"):
        return ("the join is done — the engine ruled %s: the seal certifies name, location and provenance. "
                "It owes only a tombstone. [%s]" % (ruled, reel_why))
    if ruled and ruled == _engine_token("RECOVERABLE"):
        return ("its one re-read is spent and it is older than the newest 16 - the engine still rules %s and "
                "nothing else can move it; the names the reader took stay on record, and his 10-02 keep-16 ruling "
                "sends it on to a tombstone. [%s]" % (ruled, reel_why))
    if ruled:
        return ("nothing left to join — the engine ruled %s, so the names were read and none of "
                "them can become a holding. It owes only a tombstone. [%s]" % (ruled, reel_why))
    if station == "EMPTY":
        return ("nothing to extract and the survey proved it — retro_triage walked this reel IN "
                "FULL and found zero panel frames, so the extraction contract (name, location, "
                "provenance) is satisfied vacuously. It owes only a tombstone. [%s]" % reel_why)
    return "routed from %s — %s" % (station, reel_why)


def plan(rep=None, path=None, spent=None, pinned=None, shield=None):
    """Who would be routed, who would be refused, and why. Writes NOTHING. -> dict

    -> {"ok", "route": [...], "declined": [...], "shelf", "why"}
    ⚠ `declined` IS NOT AN ERROR LIST. It is the part of the shelf that owes a route and cannot
    take one yet, which is the honest other half of any number this lane reports.
    """
    out = {"ok": False, "route": [], "declined": [], "shelf": 0, "why": ""}
    if rep is None:
        try:
            import reel_router as _rr
            # ⚠ v2770 — the store the overlay reads must be the store this lane
            # stamps into, or the plan is made against one ledger and the writes
            # land in another.
            rep = _rr.route(path=path)
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
    # A JOIN reel is this lane's only when the engine ruled NOT_A_HOLDING. The token is
    # extract_gap's, read once. A missing token routes none of them: unknown is not nothing.
    # RECOVERABLE and any other word stay where they are. They still owe a join.
    _hold = _nothing_owed_say()
    _done = _engine_token("JOINED")              # REG-2004 - a certified seal: the join is written
    _rec = _engine_token("RECOVERABLE")
    _reels = [r.get("reel") for r in (rep.get("reels") or []) if r.get("reel")]
    _spent = spent_past_window(_reels, spent, pinned, shield) if _rec else set()
    for r in (rep.get("reels") or []):
        st = r.get("station")
        _say = r.get("extractSay")
        _ruled = None
        if st == "JOIN" and _say is not None:
            if _say in (_hold, _done):
                _ruled = _say
            elif _say == _rec and r.get("reel") in _spent:
                _ruled = _say                    # REG-2004 - a spent re-read past the shield
        if st in ROUTES_FROM or _ruled:
            out["route"].append({"reel": r.get("reel"), "from": st,
                                 "capturedMs": r.get("capturedMs"),
                                 "why": _why_for(st, r.get("why") or "", ruled=_ruled)})
        elif st in BLOCKED_BY:
            out["declined"].append({"reel": r.get("reel"), "from": st,
                                    "owesFirst": BLOCKED_BY[st]})
    out["ok"] = True
    out["shelf"] = rep.get("shelf") or 0
    out["why"] = ("%d reel(s) can be routed now; %d owe a step first"
                  % (len(out["route"]), len(out["declined"])))
    return out


def apply(by, rep=None, limit=None, path=None, spent=None, pinned=None, shield=None):
    """Stamp each routable reel ROUTED, as an ACTOR. -> dict

    ⚠⚠ v3049 — THIS ASKS `may("reel.route")` NOW, and until today nothing did. The lock existed,
    scored, and displayed for 19 surfaces while `may()` was consulted at exactly THREE call sites
    in the whole tree — so eighteen locks gated nothing at all. A scouted pass found this is the
    ONE place state changes: reel_router.route()/_station_of DERIVE each reel's station and write
    nothing; the stamp into the append-only actor ledger happens only here, and both live entry
    points (control_app's triage tick and this module's CLI) funnel through it. plan() writes
    nothing and needs no guard.

    ⚠ `reel.route` is ORDINARY, not destructive: it DECIDES where a reel is, and the actual
    deleters (frame.release, prune.arm) keep their own fail-closed guards, so defence in depth
    holds. That matters because may() refuses on a STALE census too, and the census goes stale
    whenever a gate file changes — v3042's split means an ordinary lock like this one refuses on
    MERIT only, so writing a gate cannot stop his reels being routed. [[stale-reading]]
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
    # ⚠⚠ THE LOCK, ASKED AT THE ONE PLACE THAT WRITES. See the docstring for why this is the only
    # seat: plan() and reel_router.route() decide and write nothing, so a guard there would refuse
    # a thought rather than an act.
    try:
        import self_arming as _sa
        _ok, _lw = _sa.may("reel.route")
    except Exception as _e:
        # ⚠ AN UNREADABLE LOCK IS NOT AN OPEN ONE, but neither is it a reason to lose the reason.
        _ok, _lw = False, "the lock could not be read (%s), which is UNKNOWN and fails closed" % type(_e).__name__
    if not _ok:
        out["why"] = "reel.route is LOCKED — %s" % _lw
        return out
    p = plan(rep, path=path, spent=spent, pinned=pinned, shield=shield)
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
            try:
                lim = int(argv[i + 1])
            except ValueError:
                print("--limit needs a number, got %r" % argv[i + 1])
                return 2
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
    # ⚠ v2769 — `lim` WAS PARSED AND NEVER PASSED. Found by the post-ship review: a cautious
    # `--apply --limit 1` first run against an append-only store stamped EVERY routable reel.
    r = apply(by, limit=lim)
    print(json.dumps(r, indent=1)[:4000])
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
