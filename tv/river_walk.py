#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ONE FISH, FOLLOWED — where a named reel stands, what holds it, and WHO MOVES IT NEXT.

The row `frame_deleter_disagrees` asked for a driver that walks ONE named reel through the
printer's stations by calling the existing ticks in order. **That is not buildable and this file
is what is buildable instead.** Measured 2026-09-06: all five lane ticks
(`retro_triage_tick`, `vault_autoreel_tick`, `chronicle_autoread_tick`, `chronicle_autoreel_tick`,
`shadow_watch_tick`) take NO argument and each CHOOSES ITS OWN REEL. A loop that "drove a named
reel" by calling them would drive whichever reel each tick felt like while printing the named
reel's stage — a sequencer that reads as working and is not. So this WALKS and never DRIVES, and
`cannot()` says so in its own output rather than in a docstring nobody reads at runtime.

⚠⚠ IT DERIVES NOTHING AND WRITES NOTHING. Every fact below is quoted from the module that already
owns it — the stage and the hold from `reel_story` (which quotes `reel_retention.plan`), the
station and the gate from `reel_router`, the seven stations from `printer`. Re-deriving any of
them here would put a second authority on a question that already has one, which is the defect
this family of modules keeps being written to close. [[copy-drift]] §1

WHAT IT ADDS, and it is exactly one thing: **the map from a GATE to the LANE that would open it.**
`reel_router.OWES` already names what each station is waiting on — SURVEY, TRIAGE, READ, SEAL,
ROUTE, TOMBSTONE — and nothing anywhere says WHO does that work, or whether anybody does. Asking
gave the answer this file exists to publish: for most stations on his shelf, **nobody does**.

⚠ TWO QUESTIONS, ON PURPOSE, AND THEY MAY DISAGREE. `stage`/`hold` come from the RETENTION TAG
("why are we keeping these bytes"); `station` comes from the reel's OWN EVIDENCE ("where is it in
the river"). `reel_router`'s whole case is that collapsing those two let the keep-reason silently
decide the read-fate. A reel held at `swept` by retention while sitting at station CAPTURE is not
an error — it is the two answers doing their separate jobs.

    python3 tv/river_walk.py <reel>          # one fish
    python3 tv/river_walk.py <reel> --json
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

#: sentinel — "the key was not present" is not "the value was None". A printer build that predates
#: the tombstone census has no opinion about the far end; one that has the key and answered None
#: looked and could not tell. Collapsing those two would be the whole [[unknown-stays-unknown]]
#: lesson, in the module written to apply it.
_ABSENT = object()

#: THE GATE -> THE LANE. Keyed on `reel_router.STATIONS`; the gate wording is reel_router.OWES's
#: and is not repeated here.
#:
#: ⚠⚠ `consumes` IS THE PRODUCT. False does not mean the lane is broken — it means no automatic
#: lane takes ITS INPUT FROM THIS STATION, so a reel that arrives here waits until a person acts.
#: Publishing a lane name for every station would have been friendlier and would have hidden the
#: finding.
#:
#: ⚠ `owner` NAMES A FUNCTION THIS MODULE NEVER CALLS. It is a pointer for a reader, not a hook.
#: Every one of those functions selects its own reel (see the module docstring), so naming one
#: here is a statement about who would act, never a way to make it act.
LANE_OF_STATION = {
    "INTAKE": {
        "lane": "tvd-retro-triage",
        "owner": "control_app.retro_triage_tick",
        "consumes": True,
        "picks": "unread reels the survey has never walked, SMALLEST FIRST",
        "note": "the free structural survey — it spends no money",
    },
    "TRIAGE": {
        "lane": "tvd-retro-triage",
        "owner": "control_app.retro_triage_tick",
        "consumes": True,
        "picks": "unread reels the survey has never walked, SMALLEST FIRST",
        "note": "same lane as INTAKE: one survey answers both stations",
    },
    "EMPTY": {
        "lane": None,
        "owner": None,
        "consumes": False,
        "picks": None,
        "note": "the gate is ROUTE and NOTHING ROUTES. His ruling, 2026-09-05, is quoted in "
                "reel_router.OWES: a reel with nothing to read still owes a stamped record and "
                "does not leave the river. No lane opens that gate today",
    },
    "STATION": {
        "lane": "tvd-chron-autoread",
        "owner": "control_app.chronicle_autoreel_tick",
        "consumes": False,
        "picks": "reels the DURABLE SWEEP MEMORY says owe a read — never this station",
        "note": "⚠⚠ A LANE EXISTS AND THIS QUEUE IS NOT ITS INPUT. The reel sweep selects on its "
                "own predicate, so a reel can sit at STATION with the sweeper considering it "
                "finished, and the two never meet. This is the paid queue and nothing consumes "
                "it. [[the-unjoined-end]]",
    },
    "PRINTER": {
        "lane": "tvd-vault-autoread",
        "owner": "control_app.vault_autoreel_tick",
        "consumes": True,
        "picks": "reels retention tags `vault-owes` — and see `queue` below, because that set "
                 "is empty on his shelf by construction",
        "note": "the seal is written by the vault sweep. A person can still start one by hand "
                "from the console; `consumes` is about the AUTOMATIC lane only",
    },
    "JOIN": {
        "lane": None,
        "owner": None,
        "consumes": False,
        "picks": None,
        "note": "reel_router.OWES ends this gate with the word 'Code.' — the names are read and "
                "on disk and the seal does not carry them. No lane can fix that; an edit can",
    },
    "CAPTURE": {
        "lane": None,
        "owner": None,
        "consumes": False,
        "picks": None,
        "note": "REG-340: the game prints the item name only on the character panel, which the "
                "reel does not film. A capture change, never a paid read — so no reading lane "
                "will ever move a reel off this station",
    },
    "ROUTED": {
        "lane": None,
        "owner": None,
        "consumes": False,
        "picks": None,
        "note": "the gate is TOMBSTONE, and the ONLY writer of a tombstone row runs inside the "
                "deleter (`reel_retention.apply_plan` -> `_tombstone`). So a reel cannot be "
                "recorded as closed out without being removed, and removal is behind the arming "
                "lock. That weld is the gap this station has been empty for",
    },
    "TOMBSTONE": {
        "lane": None,
        "owner": None,
        "consumes": False,
        "picks": None,
        "note": "terminal. A reel only arrives here by being deleted, and a deleted reel is "
                "absent from every walk in this family — see `farEnd`",
    },
}

#: what this walk cannot establish, published BESIDE the answer. Each line is a measured limit,
#: not a disclaimer.
CANNOT = (
    "It cannot make any lane act on this reel. All five ticks — retro_triage_tick, "
    "vault_autoreel_tick, chronicle_autoread_tick, chronicle_autoreel_tick, shadow_watch_tick — "
    "take no argument and each chooses its own reel. There is no per-reel entry point to call.",
    "`consumes: true` means this station is in that lane's DECLARED candidate set. It does not "
    "mean the lane will run: the ticks' backoffs (he is playing, load, a live capture, a paid "
    "sweep, the disk floor), their retired sets and their tries bounds are not modelled here.",
    "It cannot tell you a reel finished and was never deleted. The ledger records only what the "
    "deleter removed, so 'closed out' and 'gone' are the same fact today and no surface separates "
    "them.",
    "`stage`/`hold` answer a different question from `station` and may disagree. That is the "
    "design, not a fault — see the module docstring.",
)


def _shape(reel):
    """The return shape, identical on EVERY path. REG-546: a shape that changes with the verdict
    is not a shape, and a consumer reading `walked` should not raise on the one path that means
    nothing was established."""
    return {"ok": False, "asked": reel, "reel": None, "candidates": [],
            "stage": None, "hold": None, "station": None, "printer": None,
            "next": None, "farEnd": None, "cannot": list(CANNOT), "why": ""}


def _resolve(asked, names):
    """(name, candidates, why). Exact wins; otherwise substring; AMBIGUOUS REFUSES.

    ⚠ It never picks the first of several. `printer.stream(reel)` filters by substring and would
    happily walk three reels under one question; a walk that silently answered about a different
    reel than the one asked is the worst failure available to this file.
    """
    a = str(asked or "").strip()
    if not a:
        return None, [], "no reel was named"
    if a in names:
        return a, [], ""
    hits = sorted(n for n in names if a in n)
    if not hits:
        return None, [], ("no reel on this shelf matches %r — %d reel(s) were offered"
                          % (a, len(names)))
    if len(hits) > 1:
        return None, hits, ("%r matches %d reels and this refuses to guess which one you meant"
                            % (a, len(hits)))
    return hits[0], [], ""


def _far_end(pr, router):
    """What has reached the far end, and the honest reading of the router's zero. -> dict

    ⚠⚠ THE ZERO NEEDS ITS DENOMINATOR. `reel_router` reports TOMBSTONE 0 and lists it as
    unreached; its own comment reads "nothing routes or tombstones yet". The first half is true.
    The second is a zero over REELS ON DISK: reels that were closed out are, by definition, no
    longer on the shelf every walk in this family enumerates, so this count could never have been
    anything but 0 no matter how many were closed out. [[zero-needs-a-denominator]]
    """
    cen = pr.get("tombstoned", _ABSENT) if isinstance(pr, dict) else _ABSENT
    counts = (router or {}).get("counts") or {}
    unreached = list((router or {}).get("unreached") or [])
    out = {"onShelf": {"TOMBSTONE": counts.get("TOMBSTONE"), "ROUTED": counts.get("ROUTED")},
           "routerCallsUnreached": unreached, "ledger": None, "why": ""}
    if cen is _ABSENT:
        out["why"] = ("this printer build publishes no tombstone census, so how many reels have "
                      "EVER been closed out is UNKNOWN here — not zero. The router's TOMBSTONE 0 "
                      "is a count of reels ON DISK and can never be anything else.")
        return out
    out["ledger"] = cen
    if not (isinstance(cen, dict) and cen.get("ok")):
        out["why"] = ("the tombstone ledger could not be read (%s), so the far end is UNKNOWN. "
                      "The router's TOMBSTONE 0 counts reels ON DISK either way."
                      % str((cen or {}).get("why") or "no reason given")[:100])
        return out
    out["why"] = ("%d reel(s) (%s MB) DID reach the far end and are absent from this walk because "
                  "it enumerates on-disk reels. So TOMBSTONE %s means 'none on this shelf', never "
                  "'none ever' — and ROUTED %s is the real gap: nothing records a reel as closed "
                  "out without deleting it."
                  % (cen.get("reels"), cen.get("mb"), counts.get("TOMBSTONE"),
                     counts.get("ROUTED")))
    return out


def walk(reel, hist=None):
    """Follow ONE named reel. -> dict, same shape on every path. Writes nothing, drives nothing."""
    out = _shape(reel)
    try:
        import reel_story as RS
    except Exception as e:
        out["why"] = "reel_story would not import (%s) — UNKNOWN, not an empty shelf" % str(e)[:80]
        return out
    try:
        st = RS.story(hist_dir=hist)
    except Exception as e:
        out["why"] = "reel_story.story() raised (%s) — UNKNOWN, not an empty shelf" % str(e)[:80]
        return out
    if not st.get("ok"):
        out["why"] = "the shelf could not be told: %s" % str(st.get("why"))[:140]
        return out
    rows = st.get("reels") or []
    name, cands, why = _resolve(reel, [r.get("reel") for r in rows])
    if not name:
        out["candidates"] = cands
        out["why"] = why
        return out
    out["reel"] = name
    row = next((r for r in rows if r.get("reel") == name), {})
    out["stage"] = {"stage": row.get("stage"), "stageIdx": row.get("stageIdx"),
                    "stageKnown": row.get("stageKnown"), "ladder": list(RS.STAGES)}
    out["hold"] = {
        "held": row.get("held"), "kind": row.get("holdKind"), "tag": row.get("tag"),
        "why": row.get("why"),
        # the sentence a reader actually needs: is this the pipeline working, or a real blocker
        "say": ({"policy": "HELD BY POLICY — the pipeline working as designed",
                 "evidence": "HELD BY EVIDENCE — a gap in the pipeline, about THIS reel",
                 "global": "HELD BY A SHELF-WIDE UNKNOWN — nothing here is about this reel",
                 "None": "not held"}.get(str(row.get("holdKind")), "not held")),
    }

    # the reel's POSITION, from its own evidence. A second walk of the shelf: reel_router calls
    # printer.stream() internally and this calls it again for the per-station detail. Measured
    # 0.32s + 0.23s warm — paid once, by a CLI, deliberately, rather than by re-deriving either.
    router, prep = None, None
    try:
        import reel_router as RR
        router = RR.route(hist)
    except Exception as e:
        router = {"ok": False, "why": "reel_router would not answer (%s)" % str(e)[:80]}
    if router.get("ok"):
        rrow = next((r for r in (router.get("reels") or []) if r.get("reel") == name), None)
        if rrow is None:
            out["station"] = {"station": "UNKNOWN", "owes": None,
                              "why": "the router walked the shelf and did not place this reel"}
        else:
            out["station"] = {"station": rrow.get("station"), "owes": rrow.get("owes"),
                              "why": rrow.get("why"), "sealed": rrow.get("sealed"),
                              "names": rrow.get("names"),
                              "worthReading": rrow.get("worthReading"),
                              "capturedMs": rrow.get("capturedMs"),
                              "clockFrom": rrow.get("clockFrom")}
    else:
        out["station"] = {"station": "UNKNOWN", "owes": None,
                          "why": "the router could not answer: %s"
                                 % str(router.get("why"))[:140]}

    try:
        import printer as P
        prep = P.stream(name)
    except Exception as e:
        prep = {"ok": False, "why": "printer.stream() raised (%s)" % str(e)[:80]}
    if prep.get("ok"):
        prow = next((r for r in (prep.get("rows") or []) if r.get("reel") == name), None)
        out["printer"] = {"stations": list(P.STATIONS),
                          "say": {s: (((prow or {}).get("stations") or {}).get(s) or {}).get("say")
                                  for s in P.STATIONS},
                          "why": {s: (((prow or {}).get("stations") or {}).get(s) or {}).get("why")
                                  for s in P.STATIONS}}
    else:
        out["printer"] = {"stations": [], "say": {}, "why": {},
                          "note": "the printer could not walk: %s" % str(prep.get("why"))[:140]}

    # WHO MOVES IT NEXT — the one thing this file adds.
    sta = (out["station"] or {}).get("station")
    lane = dict(LANE_OF_STATION.get(sta) or {})
    if not lane:
        lane = {"lane": None, "owner": None, "consumes": False, "picks": None,
                "note": "this station has no lane entry, which means the map was never taught "
                        "about it — UNKNOWN, never 'nobody is needed'"}
    # the PRINTER station's lane has a queue that is empty on his shelf BY CONSTRUCTION, and
    # saying "a lane owns this" without that is the half-truth this whole file is against.
    # ⚠ THIS IS A CANDIDATE-SET CHECK, NOT A SIMULATION OF THE TICK. The vault lane's work list is
    # retention's `vault-owes` set; that tag is read here from reel_story, which quotes the same
    # reel_retention.plan() the lane's own selector quotes. It models none of the tick's backoffs.
    if sta == "PRINTER":
        owes = sum(1 for r in rows if r.get("tag") == "vault-owes")
        lane["queue"] = {
            "tag": "vault-owes", "carryingIt": owes, "shelf": len(rows),
            "why": ("%d of %d reels carry the tag this lane selects on. %s"
                    % (owes, len(rows),
                       ("The lane's queue is EMPTY: retention's rules are first-match-wins and "
                        "`vault-owes` is the LAST one, so every reel matches something earlier. "
                        "The lane publishes owed:0, which reads as a healthy idle lane, and this "
                        "reel waits for a seal nothing will write."
                        if not owes else "The lane has work it could pick up.")))}
        if not owes:
            lane["consumes"] = False
    out["next"] = lane
    out["farEnd"] = _far_end(prep if isinstance(prep, dict) else {}, router)
    out["ok"] = True
    out["why"] = ("%s sits at %s (retention calls it %s). %s"
                  % (name, sta, out["stage"].get("stage"),
                     ("the next move is owed by %s" % lane.get("owner")) if lane.get("consumes")
                     else "NO AUTOMATIC LANE takes its input from this station"))
    return out


def main(argv):
    args = [a for a in argv if not a.startswith("-")]
    if not args:
        print("\nusage: python3 tv/river_walk.py <reel> [--json]\n")
        return 2
    r = walk(args[0])
    if "--json" in argv:
        print(json.dumps(r, indent=2, sort_keys=True, default=str))
        return 0
    print("\nTHE RIVER, ONE FISH — %s\n" % (r.get("reel") or r.get("asked")))
    if not r["ok"]:
        print("  %s" % r["why"])
        for c in r["candidates"]:
            print("     candidate: %s" % c)
        print()
        return 1
    h, s, n = r["hold"], r["station"], r["next"]
    print("  STAGE     %-12s (%s)" % (r["stage"]["stage"], "known" if r["stage"]["stageKnown"]
                                      else "⚠ a verdict the board was never taught"))
    print("  HOLD      %s" % h["say"])
    print("            tag %s · %s" % (h["tag"], str(h["why"] or "")[:100]))
    print("  STATION   %-10s owes: %s" % (s["station"], str(s["owes"] or "")[:90]))
    print("            %s" % str(s.get("why") or "")[:110])
    print("  NEXT      %s" % ("%s (%s)" % (n.get("lane"), n.get("owner")) if n.get("consumes")
                              else "⚠ NO AUTOMATIC LANE"))
    print("            %s" % str(n.get("note") or "")[:150])
    if n.get("queue"):
        print("            queue: %s" % str(n["queue"]["why"])[:150])
    if r["printer"].get("say"):
        print("\n  the printer's seven stations:")
        for st in r["printer"]["stations"]:
            print("     %-10s %-14s %s" % (st, r["printer"]["say"].get(st),
                                           str(r["printer"]["why"].get(st) or "")[:80]))
    print("\n  THE FAR END")
    print("     %s" % str(r["farEnd"]["why"])[:220])
    print("\n  ⚠ WHAT THIS WALK CANNOT KNOW")
    for c in r["cannot"]:
        print("     · %s" % c[:150])
    print()
    return 0


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
