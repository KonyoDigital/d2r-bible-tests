#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""THE STAMP — a reel's JOURNEY, written down, one row per station it actually reached.

His ask, 2026-09-06: *"this maybe is a good design for a STAMPING PROCESS for each reel ive said
this before.. a visual and backend stamp even for each so they go through story line and synced
from station and down to tombstone eventually"*.

⚠⚠ WHAT WAS MISSING, MEASURED. `reel_router.route()` answers WHERE EVERY REEL IS, correctly, on
every call — and remembers nothing. Run it twice and the second answer cannot tell you whether a
reel moved between the two, because there was no first answer to compare against. So a reel has a
POSITION and has never had a JOURNEY: nothing in this tree can say "this reel reached STATION on
the 4th and PRINTER on the 6th". His sentence is about the journey — *"synced from station and
down to tombstone"* — and the journey is what did not exist.

    reel_router   WHERE IS IT NOW      recomputed every call, stored nowhere
    river_walk    WHO WOULD MOVE IT    the gate -> lane map, read-only, stores nothing
    river_stamp   WHERE HAS IT BEEN    THIS FILE. the only one that remembers.

=== THE THREE RULES THIS STORE IS BUILT ON, AND WHY EACH IS NOT NEGOTIABLE ===

1. **APPEND-ONLY MEANS NO SECOND MODE, NOT "MOSTLY APPEND".** The sibling free-space series appends
   and then trims by age — correct there, because an old free-space reading is genuinely worthless.
   It would be catastrophic here: trimming the oldest rows deletes the BEGINNING of every reel's
   journey, which is the half a journey is for. So this file opens the store `"a"` and never `"w"`,
   there is no trim, and the ceiling REFUSES a write rather than making room by forgetting.
   A store that can drop its own earliest evidence is a cache wearing a ledger's name.

2. **A STAMP RECORDS A TRANSITION, SO IT MUST NAME WHAT MOVED THE REEL.** `by` is required and an
   empty one is refused, exactly as the lane heartbeat refuses an unnamed lane. A row saying "this
   reel reached PRINTER" with nobody attached cannot answer the only question anyone will ask of
   it later, which is *who did that, and can it do it again*. `river_walk.LANE_OF_STATION` names
   the automatic lanes; `by` is not restricted to them, because a person at the console and a CLI
   run are also real causes and pretending otherwise would push them into a lane's name.

3. **NOTHING MOVED IS NOT AN EVENT.** Re-stamping a reel at the station it is already at writes
   NOTHING and says so (`wrote: False`, `ok: True`). The river is walked on a timer; a store that
   wrote a row per walk would hold ten thousand rows saying "still at CAPTURE" and the journey
   would be unreadable inside its own noise.
   ⚠ A GENUINE RE-ENTRY IS A DIFFERENT FACT AND IS KEPT. A reel that goes PRINTER -> TRIAGE ->
   PRINTER gets a SECOND PRINTER row, because it arrived there twice and that is what happened.
   The dedupe is on the reel's CURRENT station, never on "(reel, station) has been seen before" —
   the second reading would silently erase every regression, and a regression is the single most
   interesting thing a journey can contain. `reel_router.OWES["EMPTY"]` already says the EMPTY
   verdict is REOPENABLE, so re-entry is a state this river is documented to produce.

=== UNKNOWN IS A POSITION AND IT GETS STAMPED ===
`reel_router` returns `UNKNOWN` for a reel whose evidence could not be read, and is emphatic that
this is never folded into a working total. Same here: UNKNOWN is stampable — "we walked the river
on the 6th and could not place this reel" is a real, dated finding — and `census()` reports it
BESIDE the counts, never inside them. A store that refused to stamp UNKNOWN would leave those reels
with a journey that skips the days nobody could see them, which reads as continuity that did not
happen. [[unknown-stays-unknown]]

=== WHAT IT DOES NOT DO, SAID HERE RATHER THAN DISCOVERED LATER ===
⛔ IT ARMS NOTHING, READS NO FOOTAGE, SPENDS NO MONEY AND DELETES NOTHING. It records where the
router already said a reel was. It cannot move a reel; `river_walk.CANNOT` explains why nothing in
this family can (all five lane ticks take no argument and each picks its own reel).
⛔ IT CANNOT STAMP TOMBSTONE FROM THE FLEET WALK, and that is a property of the tree, not a
shortcoming here: the only writer of a tombstone row runs INSIDE the deleter, milliseconds before
the bytes go, so a reel is recorded as closed out and removed in one act. `run()` walks the SHELF,
and a tombstoned reel is by definition off the shelf — so it is absent from the walk that would
stamp it. `stamp(reel, "TOMBSTONE", by=...)` works and is the honest entry point the day that weld
is separated; until then TOMBSTONE stays reachable by hand and unreachable by the river.

    python3 tv/river_stamp.py                     # the census — where the fleet has been
    python3 tv/river_stamp.py <reel>              # one reel's journey, oldest first
    python3 tv/river_stamp.py --run <lane-name>   # walk the river once and stamp what moved
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

STORE = "river_stamp.jsonl"

#: ⚠ A SAFETY NET, NOT A POLICY, AND IT REFUSES RATHER THAN TRIMS. With the dedupe above, the store
#: grows by TRANSITIONS, not by walks: 40 reels through 9 stations is 360 rows even if every reel
#: traverses the whole river. Reaching this ceiling means something is oscillating a reel between
#: two stations, and the right response to that is to STOP WRITING AND SAY SO — not to make room by
#: deleting the earliest evidence, which is the only copy of how the oscillation started.
_CEILING = 500000


def _store_path(path=None):
    """Where the journey is remembered. -> path

    ⚠ RESOLVED AT CALL TIME, NEVER AT IMPORT. Its sibling free-space series was bound from HERE at
    import and so ignored the fixture root entirely — an env honoured only at import is a redirect
    that silently does not take, and the consequence there was a gate run writing into his real
    tree. The rule cost something once; it is not being re-learned here.
    """
    if path:
        return path
    try:
        import tv_diablo as _tvd
        return os.path.join(_tvd._fixture_root(HERE), STORE)
    except Exception:
        return os.path.join(HERE, STORE)


def stations():
    """The one station vocabulary. -> (tuple|None, why)

    ⚠⚠ IT IS IMPORTED, NEVER COPIED, AND THE GATE CHECKS THAT BY IDENTITY. A hardcoded tuple here
    would be a second authority on what a station IS — and the day someone adds a station to the
    router, this store would start refusing it with a message naming a vocabulary that no longer
    exists. [[copy-drift]] §1: one owner, everyone else quotes.
    ⚠ If the router will not import, the vocabulary is UNKNOWN and every `stamp()` REFUSES. It does
    not fall back to a guess — a store that invents its own vocabulary when the owner is missing is
    how two vocabularies get born.
    """
    try:
        import reel_router as _rr
        return tuple(_rr.STATIONS) + (_rr.UNKNOWN,), ""
    except Exception as exc:
        return None, ("reel_router would not import (%s), so what counts as a station is UNKNOWN "
                      "and nothing may be stamped" % type(exc).__name__)


def rows(path=None):
    """Every stamp ever written, IN FILE ORDER. -> dict

    ⚠⚠ FILE ORDER IS THE HISTORY. `at` is a READING taken at write time; the append order is the
    order the events happened in. Sorting by `at` would put a second authority on sequence, and the
    two disagree the moment two stamps land in the same millisecond or the clock steps backwards.
    So the rows come back as written, and `outOfOrder` publishes how many times `at` contradicts
    the append order instead of silently resolving it. A contradiction is the finding.

    ⚠ AN UNPARSEABLE LINE IS COUNTED, NEVER SKIPPED SILENTLY. `unparsed > 0` makes every count
    derived from this a FLOOR rather than a total, and a consumer that does not say so is
    publishing a number nobody measured.
    """
    p = _store_path(path)
    out = {"ok": False, "rows": [], "n": 0, "unparsed": 0, "outOfOrder": 0,
           "path": p, "everStamped": None, "why": ""}
    if not os.path.exists(p):
        # ⚠ MEASURED-AND-EMPTY, not unreadable. The store not existing yet is a fact about the
        # river (nothing has ever been stamped), and it is a different fact from "the store is
        # there and would not open" — which is the branch below and answers ok=False.
        out.update({"ok": True, "everStamped": False,
                    "why": "no stamp has ever been recorded — the river has not been walked with "
                           "a stamper attached. That is measured-and-zero, not unreadable"})
        return out
    try:
        with open(p, encoding="utf-8") as fh:
            lines = fh.readlines()
    except Exception as exc:
        out["why"] = ("the stamp store exists and would not read (%s) — every count below this is "
                      "UNKNOWN, never zero" % type(exc).__name__)
        return out
    got, bad, last_at = [], 0, None
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        try:
            r = json.loads(ln)
        except Exception:
            bad += 1
            continue
        if not isinstance(r, dict) or not r.get("reel") or not r.get("station"):
            bad += 1
            continue
        got.append(r)
        at = r.get("at")
        if isinstance(at, (int, float)) and not isinstance(at, bool):
            if last_at is not None and at < last_at:
                out["outOfOrder"] += 1
            last_at = at
    out.update({"ok": True, "rows": got, "n": len(got), "unparsed": bad,
                "everStamped": bool(got)})
    if bad:
        out["why"] = ("%d line(s) in the stamp store would not parse — every count taken from it "
                      "is a FLOOR, not a total" % bad)
    return out


def history(reel, path=None):
    """One reel's journey, oldest first. -> dict

    This is "the river" for a single fish: the ordered stations it has actually reached, each with
    when, and with what moved it there.
    """
    reel = str(reel or "").strip()
    out = {"ok": False, "reel": reel, "stations": [], "n": 0, "current": None,
           "unparsed": 0, "outOfOrder": 0, "why": ""}
    if not reel:
        out["why"] = "no reel was named, so there is no journey to look up"
        return out
    rep = rows(path)
    if not rep["ok"]:
        out["why"] = "UNKNOWN, not an empty journey — %s" % rep["why"]
        return out
    mine = [r for r in rep["rows"] if str(r.get("reel")) == reel]
    out.update({"ok": True, "stations": mine, "n": len(mine),
                "current": (mine[-1].get("station") if mine else None),
                "unparsed": rep["unparsed"], "outOfOrder": rep["outOfOrder"]})
    if not mine:
        # ⚠ NEVER STAMPED IS NOT "AT NO STATION". `current: None` here means this reel has no row
        # in the store — which is a different fact from the router placing it at UNKNOWN, and a
        # consumer must be able to tell those apart. The sentence says which one this is.
        out["why"] = ("this reel has no stamp at all — it has never been walked with a stamper "
                      "attached. `current` is None because nobody looked, not because it is "
                      "nowhere")
    elif rep["unparsed"]:
        out["why"] = rep["why"]
    return out


def current(reel, path=None):
    """The station this reel was last stamped at. -> (station|None, why)

    ⚠ None HAS TWO CAUSES AND THE SENTENCE SEPARATES THEM: never stamped, or the store could not be
    read. Collapsing them would let an unreadable store read as a fresh shelf, and then `stamp()`
    would happily write a duplicate for every reel on it.
    """
    h = history(reel, path)
    if not h["ok"]:
        return None, h["why"]
    return h["current"], h["why"]


def stamp(reel, station, by, why=None, at=None, path=None, observed=False):
    """Record that `reel` reached `station`, and WHO put it there. -> dict

    ⚠⚠ `observed` SEPARATES *WHO MOVED IT* FROM *WHO SAW IT MOVE*, AND THAT DISTINCTION IS NOT
    PEDANTRY. A lane that has just acted on a reel knows it caused the transition; the FLEET WALK
    does not — it compares the router's answer against the store and finds a reel somewhere new.
    It cannot tell whether a lane moved it, a person did, or the evidence underneath simply
    changed. Writing the walker's name into `by` unqualified would put a CAUSAL CLAIM nobody
    measured into an append-only record, where it can never be corrected — the most expensive
    shape [[unknown-stays-unknown]] takes, because a durable wrong answer outlives the person who
    could have said it was a guess.

    So every row says which kind it is:
        byKind "actor"     `by` acted on this reel and then stamped it. cause, measured.
        byKind "observer"  `by` walked the river and found it here. position, measured; cause NOT.
    `run()` writes ONLY observer rows, always, and the gate holds it to that.

    -> {"ok", "wrote", "row", "from", "why"} — and the three outcomes are distinguishable on
    purpose:
        ok=False wrote=False   REFUSED. bad input, or the store could not be read.
        ok=True  wrote=False   NOTHING MOVED. it was already there. not an error, not an event.
        ok=True  wrote=True    a transition, recorded.
    A caller that only checks `ok` cannot tell a no-op from a write, which is why `wrote` exists
    beside it rather than being inferred from a truthy row.
    """
    out = {"ok": False, "wrote": False, "row": None, "from": None, "why": ""}
    reel = str(reel or "").strip()
    station = str(station or "").strip()
    by = str(by or "").strip()
    if not reel:
        out["why"] = "a stamp with no reel names nothing and could never be looked up"
        return out
    if not by:
        # ⚠ THE WHOLE POINT OF THE ROW. His words were "so they go through story line" — a story
        # needs a cause. An unattributed stamp cannot answer whether the thing that moved this reel
        # can move the next one, which is the only reason to keep the record.
        out["why"] = ("a stamp with no `by` cannot say WHAT MOVED THE REEL, which is the fact the "
                      "row exists to carry. Name the lane, the CLI or the person")
        return out
    vocab, vwhy = stations()
    if vocab is None:
        out["why"] = vwhy
        return out
    if station not in vocab:
        out["why"] = ("%r is not a station. The river is: %s" % (station, ", ".join(vocab)))
        return out
    rep = rows(path)
    if not rep["ok"]:
        # ⚠⚠ REFUSE, DO NOT WRITE BLIND. Without reading the store there is no way to know the
        # reel's current station, so the dedupe below cannot be enforced — and an append that
        # cannot dedupe turns every timer tick into a row. A store that keeps writing while it
        # cannot read itself corrupts fastest exactly when it is already broken.
        out["why"] = "refusing to stamp: %s" % rep["why"]
        return out
    if rep["n"] >= _CEILING:
        out["why"] = ("the stamp store has reached its %d-row ceiling. It is APPEND-ONLY, so "
                      "nothing here will delete the earliest rows to make room — that would erase "
                      "the beginning of every journey. Something is oscillating a reel between "
                      "stations; that is the finding" % _CEILING)
        return out
    mine = [r for r in rep["rows"] if str(r.get("reel")) == reel]
    prev = mine[-1].get("station") if mine else None
    out["from"] = prev
    if prev == station:
        out.update({"ok": True, "why": "already at %s — nothing moved, so nothing was written"
                                       % station})
        return out
    seq = 0
    for r in rep["rows"]:
        s = r.get("seq")
        if isinstance(s, int) and not isinstance(s, bool) and s > seq:
            seq = s
    row = {"at": int(at if at is not None else time.time() * 1000),
           "seq": seq + 1, "reel": reel, "station": station, "from": prev,
           "by": by, "byKind": ("observer" if observed else "actor"),
           "why": (str(why)[:400] if why else None)}
    p = _store_path(path)
    try:
        d = os.path.dirname(p)
        if d and not os.path.isdir(d):
            os.makedirs(d)
        # ⚠⚠ "a", AND THERE IS NO OTHER MODE IN THIS FILE. `open(p, "w")` empties the target BEFORE
        # anything is computed — it has already destroyed a 6 MB file in this tree once. Here it
        # would destroy every journey. The gate asserts by AST that this module opens its store in
        # append mode ONLY, because "we always append" is a promise and the mode is a fact.
        with open(p, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row) + "\n")
    except Exception as exc:
        out["why"] = "the stamp would not write (%s)" % type(exc).__name__
        return out
    out.update({"ok": True, "wrote": True, "row": row,
                "why": "%s -> %s by %s" % (prev or "(first stamp)", station, by)})
    return out


def census(path=None):
    """Where the fleet has been. -> dict

    TWO censuses, published side by side and NEVER folded into one:
      · `counts`  — per station, how many reels are THERE NOW (their most recent stamp)
      · `visits`  — per station, how many times any reel has EVER been stamped there
    They answer different questions. A station with `counts 0` and `visits 30` is a station reels
    pass THROUGH; one with `counts 11, visits 11` is a station reels arrive at and stop. Reporting
    a single number would have hidden exactly that difference.

    ⚠ `unknown` IS BESIDE THE COUNTS, NEVER INSIDE THEM — the router's own rule, kept here so a
    total taken from this store cannot quietly include reels nobody could place.
    ⚠ `unstamped` IS NOT COMPUTABLE HERE and is not guessed. This store knows only what it has been
    told; how many reels exist is the shelf's question, and `run()` is where the two meet.
    """
    out = {"ok": False, "counts": None, "visits": None, "unknown": None, "reels": None,
           "stamps": None, "unparsed": None, "everStamped": None, "unreached": None, "why": ""}
    vocab, vwhy = stations()
    rep = rows(path)
    if not rep["ok"]:
        out["why"] = "UNKNOWN, not an empty river — %s" % rep["why"]
        return out
    if vocab is None:
        out["why"] = vwhy
        return out
    last, visits = {}, {s: 0 for s in vocab}
    for r in rep["rows"]:
        st = str(r.get("station"))
        if st in visits:
            visits[st] += 1
        last[str(r.get("reel"))] = st
    counts = {s: 0 for s in vocab}
    for st in last.values():
        if st in counts:
            counts[st] += 1
    unknown = counts.pop("UNKNOWN", 0)
    visits.pop("UNKNOWN", None)
    out.update({"ok": True, "counts": counts, "visits": visits, "unknown": unknown,
                "reels": len(last), "stamps": rep["n"], "unparsed": rep["unparsed"],
                "everStamped": rep["everStamped"], "why": rep["why"]})
    # ⚠ NAME THE STATIONS NOTHING HAS EVER REACHED — the router's rule, and for the same reason.
    # A 0 beside ROUTED must not read as "none waiting there"; it reads as "no reel has ever been
    # recorded arriving", which on this shelf is a statement about the weld at the far end.
    out["unreached"] = [s for s in counts if visits.get(s, 0) == 0]
    return out


def run(by, rep=None, path=None):
    """Walk the river ONCE and stamp every reel at the station it is at. -> dict

    ⚠⚠ THIS IS THE JOIN, AND IT IS THE ONLY THING IN THE FAMILY THAT WRITES. The router answers and
    forgets; this is what makes the answer durable. It is FREE — it reads no footage, calls no
    model, and moves no reel. It records where the router already said each reel was.

    ⚠ `by` IS REQUIRED AND HAS NO DEFAULT. A default would put the same word on a timer's walk and
    a person's, and then the store could not answer which of them was moving the river.

    ⚠ `rep` IS ACCEPTED SO A HARNESS CAN HAND IN A ROUTE REPORT and never touch his shelf. When it
    is None the live router is walked. It is NOT a hist/shelf argument: `reel_router._evidence`
    refuses a mismatched shelf precisely because a fixture's clocks joined to the live shelf's
    evidence would grade his 40 real reels and pass.

    ⚠⚠ EVERY ROW THIS WRITES IS `byKind: "observer"`, WITHOUT AN OPTION TO SAY OTHERWISE. A walk
    compares the router's answer to the store and finds a reel somewhere new; it did not move it
    and cannot know what did. Letting a caller pass `observed=False` here would let the walker's
    name become a causal claim in a record that can never be corrected. A LANE that actually acted
    calls `stamp()` directly, one reel, and that row is the `actor` one.
    """
    out = {"ok": False, "moved": None, "unchanged": None, "refused": None, "shelf": None,
           "transitions": [], "refusals": [], "by": str(by or "").strip(), "why": ""}
    if not out["by"]:
        out["why"] = ("run() needs a `by` — the walk that stamps must name itself or the rows it "
                      "writes cannot say what moved anything")
        return out
    if rep is None:
        try:
            import reel_router as _rr
            rep = _rr.route()
        except Exception as exc:
            out["why"] = ("the router would not answer (%s), so the river could not be walked — "
                          "UNKNOWN, never an empty shelf" % type(exc).__name__)
            return out
    if not (rep or {}).get("ok"):
        out["why"] = ("the router could not place the shelf, so nothing was stamped — UNKNOWN, "
                      "never an empty shelf. %s" % str((rep or {}).get("why") or "")[:200])
        return out
    moved = unchanged = refused = 0
    for r in (rep.get("reels") or []):
        res = stamp(r.get("reel"), r.get("station"), out["by"], why=r.get("why"), path=path,
                    observed=True)
        if not res["ok"]:
            refused += 1
            out["refusals"].append({"reel": r.get("reel"), "why": res["why"]})
        elif res["wrote"]:
            moved += 1
            out["transitions"].append({"reel": r.get("reel"), "from": res["from"],
                                       "to": r.get("station")})
        else:
            unchanged += 1
    out.update({"ok": True, "moved": moved, "unchanged": unchanged, "refused": refused,
                "shelf": len(rep.get("reels") or [])})
    out["why"] = ("%d reel(s) changed station and were stamped · %d were already where the store "
                  "said · %d refused" % (moved, unchanged, refused))
    return out


def _p_census(c):
    if not c["ok"]:
        print("  UNKNOWN — %s\n" % c["why"])
        return 2
    print("  %-10s %6s %8s" % ("STATION", "NOW", "VISITS"))
    for s, n in c["counts"].items():
        print("  %-10s %6d %8d" % (s, n, c["visits"].get(s, 0)))
    print("  %-10s %6d %8s   position unmeasured — never folded into a total"
          % ("UNKNOWN", c["unknown"], "-"))
    print("\n  %d reel(s) stamped · %d row(s) · %d unparsed"
          % (c["reels"], c["stamps"], c["unparsed"]))
    if c["unreached"]:
        print("  NEVER REACHED (a 0 here is not 'none waiting'): %s" % ", ".join(c["unreached"]))
    if c["why"]:
        print("  %s" % c["why"])
    return 0


def main(argv):
    print("\nRIVER STAMP — where each reel has BEEN, not where it is\n")
    if argv and argv[0] == "--run":
        by = argv[1] if len(argv) > 1 else ""
        r = run(by)
        if not r["ok"]:
            print("  REFUSED — %s\n" % r["why"])
            return 2
        print("  walked as %r: %s\n" % (r["by"], r["why"]))
        for t in r["transitions"][:20]:
            print("    %-34s %s -> %s" % (t["reel"][:34], t["from"] or "(first)", t["to"]))
        print()
        return 0
    if argv and not argv[0].startswith("-"):
        h = history(argv[0])
        if not h["ok"]:
            print("  UNKNOWN — %s\n" % h["why"])
            return 2
        print("  %s — %d stamp(s), oldest first\n" % (h["reel"], h["n"]))
        for r in h["stations"]:
            print("    #%-4d %-10s by %-24s %s"
                  % (r.get("seq") or 0, r.get("station"), str(r.get("by"))[:24],
                     time.strftime("%Y-%m-%d %H:%M", time.localtime((r.get("at") or 0) / 1000.0))))
        if h["why"]:
            print("\n  %s" % h["why"])
        print()
        return 0
    rc = _p_census(census())
    print()
    return rc


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
