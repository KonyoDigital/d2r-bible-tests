# -*- coding: utf-8 -*-
"""TWO READERS, ONE BANKING STORE, AND ONLY ONE OF THEM IS WIRED TO IT.

Konyo, 2026-09-07: *"if it cant be witnessed 3 times then yes it can end up there.. but if it
witnessesed three times it automatically tallys itself right?"* — and earlier, the standing
instruction this closes: *"the routing and funnel and main pipeline should still go through it
regardless of the paid reads.. i want it filtered and then stamped unified logic."*

=== THE GAP, STATED EXACTLY ===
The auto-tally lane EXISTS and works:

    vault sweep -> vault_accum.json -> vault_retro.gate(KEEP_CONF_FLOOR, KEEP_MIN_WITNESSES)
                -> control_app.vault_apply -> the board's own vaultAccumApply (dated, merge-max,
                   undoable — the same tick his hand uses)

But `vault_accum.json` is written **by the vault lane during a PAID SWEEP** (write_census.py:55).
The 119 item names sitting unbanked were read by the **deep** reader into the journal ring, which
is a different lane, and the accumulator has no other feeder. So those names were never REFUSED —
**they were never judged.** That distinction is the whole finding: a refusal is a verdict, and
nothing here ever reached a verdict. [[the-unjoined-end]] [[plumbing-with-no-tap]]

=== ⛔ WHY THIS MODULE REPORTS AND NEVER WRITES ===
Banking is not free in the direction that matters. `reel_retention` holds a reel with the reason
`rows-not-banked`, so **landing a name in the accumulator RELEASES that reel's footage for
pruning.** Wiring 119 unjudged names straight into a durable store would hand a deleter 119 new
permissions in one move, and footage has no un-delete. The split is made visible first, on his real
data, and the write stays with the existing witnessed machinery.
[[unknown-stays-unknown]] [[feedback-verify-not-proxy]]

=== WHAT IT MEASURES, AND THE TWO NUMBERS THAT MATTER ===
Measured on his journal today — 151 deep rows carrying names, every one with a `conf` between
0.60 and 0.95 against a 0.55 floor, so **confidence is not what is stopping anything**:

    PANEL names, distinct        42
    clearing 3 witnesses          3     Horadric Cube (11) · Tome of Town Portal (9) ·
                                        Tome of Identify (7)
    refused, to the manual lane  39     Harlequin Crest · Hellfire Torch · War Traveler ·
                                        Goldwrap · Magefist · Lionheart · Crescent Moon ...

⚠⚠ **THE THREE THAT PASS ARE THE THREE EVERY CHARACTER CARRIES.** They corroborate because they are
UBIQUITOUS. A rare unique sits in one stash tab and is filmed ONCE, so single-sighting is the NORMAL
case for exactly the items a grail tally exists to count. The witness bar is therefore
ANTI-CORRELATED with grail value — and that is not a bug in the bar. `KEEP_MIN_WITNESSES` was
derived for a DELETER (may this footage be destroyed); reusing it as a TALLY bar borrows a threshold
built for a different question. **His ruling settles it: manual is the path for rares.**

PANEL only, deliberately: a FLOOR name has no cell to name, so it is a sighting and not a holding —
`console_doctor`'s own words, from his: *"if its a FLOOR ITEM with no stash/inventory open then
obviously it cant be in the same exact route"*.
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass


def evidence(journal_paths=None):
    """Deep-lane PANEL names as gate-shaped evidence rows. -> ({name: [row]}, why)

    ⚠ THE ROW SHAPE IS THE GATE'S, NOT MINE. `vault_retro.gate` reads `witness` (falling back to
    `session`) and `conf`. Inventing a different shape here would mean the numbers this module
    prints were produced by a reimplementation of the gate rather than by the gate, and a private
    copy of a rule drifts from it. [[feedback-verify-not-proxy]]
    """
    try:
        import control_app as CA
        import extract_gap as EG
    except Exception as e:
        return None, "the journal reader could not be imported (%s)" % str(e)[:80]
    try:
        paths = journal_paths if journal_paths is not None else [
            p for p in (CA._journal_ring() or []) if os.path.isfile(p)]
    except Exception as e:
        return None, "the journal ring could not be resolved (%s)" % str(e)[:80]
    if not paths:
        # ⚠ None, never {}. "no journal on this venue" and "a journal holding no names" are
        # opposite facts, and only the second is a finding. [[unknown-stays-unknown]]
        return None, "there is no journal ring on this venue"

    out = {}
    rows = 0
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
                    names = [str(x).strip() for x in (r.get("names") or []) if str(x).strip()]
                    if not sid or not names:
                        continue
                    if str(r.get("scene") or "").strip().lower() not in EG.PANEL_SCENES:
                        continue
                    rows += 1
                    # ⚠⚠ v2983 — HIS RULING, 2026-09-12: *"these are specifically locked items
                    # within the INVENTORY specifically and not stashed items.. they are inside
                    # and witnessed within the inventory for sure."*
                    #
                    # `scene` IS A PROPERTY OF THE FRAME, NOT OF THE ITEM. One deep row carries one
                    # `scene` and a LIST of names, so every name read from that frame inherited the
                    # frame's single label. In D2R the stash panel displays the inventory beside it,
                    # so a single frame legitimately holds items from BOTH containers — and the lane
                    # filed all of them under whichever panel it thought it was looking at.
                    #
                    # The producer already recorded the right answer and nobody read it:
                    # `names_loc` is a PER-NAME container map, present on 125 of 151 deep rows.
                    # MEASURED on his journal, frame `scene` vs per-name `names_loc`:
                    #     stash / inventory    56   <- DISAGREE
                    #     inventory / inventory 31
                    #     stash / stash        12   <- the ONLY genuinely-stash sightings
                    #     inventory / floor     7   <- DISAGREE
                    #     stash / equipped      2 · stash / floor 1 · inventory / equipped 1
                    # 66 of 110 panel sightings carried a container contradicting the item's own.
                    #
                    # HIS THREE ARE THE PROOF, because they are the only names whose answer is
                    # KNOWN — the cube and the tomes are carried, permanently, and can never sit in
                    # a stash. `names_loc` says `inventory` on all 58 of their sightings. `scene`
                    # says `stash` on 34 of them. He was right and the system already agreed with
                    # him; the lane was the only thing that did not.
                    #
                    # `scene` is KEPT, not replaced — it is a true fact about the frame, and the
                    # pair is worth more than either half: a name whose frame and item disagree is
                    # exactly a name seen in one panel while living in another.
                    # [[the-unjoined-end]] [[label-outlived-referent]]
                    _loc = r.get("names_loc")
                    _loc = _loc if isinstance(_loc, dict) else {}
                    for nm in names:
                        # ⚠ "" is NOT "floor" and NOT the scene. A name the producer did not place
                        # is UNPLACED, and a guess here would be indistinguishable from a reading.
                        # [[unknown-stays-unknown]]
                        out.setdefault(nm, []).append(
                            {"session": sid, "conf": r.get("conf"),
                             "scene": str(r.get("scene") or ""), "ts": r.get("ts"),
                             "loc": str(_loc.get(nm) or "").strip().lower() or None})
        except Exception:
            continue
    return out, ("%d deep PANEL row(s) carrying names" % rows)


#: Locked-inventory fixtures — HIS RULING, 2026-09-07: *"these are locked inventory only and
#: specifically items.. the tombs and the hordaic cub"*. They are carried permanently, so they
#: appear in EVERY session by construction. That is why they are the only names clearing a
#: corroboration bar, and it is also why clearing it means nothing about them.
#:
#: ⚠⚠ MEASURED, AND IT IS NOT A ROUNDING ERROR: these three are **58 of the 110 sightings** the
#: reader produced across 42 PANEL names — **52.7%**. Over half the reader's output is furniture.
#: The 15 grail-eligible names account for 20 sightings between them.
#:
#: ⚠ A DECLARED LIST, NOT A HEURISTIC. "appears in most sessions" would also describe a genuinely
#: common find, and would grow silently into a filter nobody can audit. Three names, his words,
#: and a law asserts the list stays closed.
#:
#: ⚠⚠ HIS RULING, 2026-09-12, REFINING THE ABOVE — THEY ARE NOT NOISE, THEY ARE THE ONLY GROUND
#: TRUTH THIS READER HAS: *"these are specifically locked items within the INVENTORY specifically
#: and not stashed items.. they are inside and witnessed within the inventory for sure. and the
#: slot itendity for them should also have been tallied and logged and ledgered as such so there is
#: that distinigushed difference."*
#:
#: Not ticking them stays right. Treating them as 52.7% of wasted output was wrong. They are the
#: only three names whose TRUE CONTAINER IS KNOWN — carried permanently, so they can never sit in
#: a stash — which makes them a known-answer probe for the container reader. Pointed at them, the
#: reader failed: the frame `scene` the lane was using said `stash` for 34 of their 58 sightings,
#: while the producer's per-name `names_loc` said `inventory` for all 58. He was right, the system
#: had already agreed with him, and only the lane disagreed. v2983 joins them; see evidence().
#:
#: ⛔ THE SLOT HALF OF HIS RULING IS NOT BUILT AND CANNOT BE BUILT HERE. Measured 2026-09-12: of
#: 151 deep rows carrying names, **0** carry any slot/cell/grid/xy/rect field. There is no grid
#: coordinate anywhere in the journal to join, so a slot ledger is a CAPTURE-AND-EXTRACTION change,
#: not a wiring change — the same shape of answer as REG-340 ("that is a capture change, not a code
#: change, and it is the real prerequisite"). Recorded as unbuilt rather than half-built.
FURNITURE = ("horadric cube", "tome of identify", "tome of town portal")


def rosters():
    """All three rosters as {normalised: canonical}. -> (dict_of_rosters, why)

    ⚠⚠ UNKNOWN ON FAILURE, NEVER AN EMPTY ROSTER. `chronicle_resolve.load_roster` RAISES rather
    than returning {} for exactly this reason, in its own words: *"an empty roster would silently
    classify every name as debris and retire his entire queue, which is the loudest possible
    failure wearing the quietest possible face."*

    ⚠ AND I TRIPPED OVER IT WRITING THIS. A first pass called `CR.roster()` / `CR.set_roster()`
    through `hasattr`, which are not the function names — the getattr fallback handed back None, the
    guard was bypassed, and the measurement read "uniques=0 sets=0, 42 of 42 NEITHER". A clean zero
    produced by asking the wrong question. [[zero-needs-a-denominator]] [[source-reading-guard]]

    ⚠ THE RUNEWORD ROSTER IS LOADED HERE AND NOWHERE ELSE. `chronicle_resolve` knows uniques and
    sets only, so a runeword classified against those two comes back NEITHER — Lionheart did, and
    it is a real roster name. Three ledgers, three rosters.
    """
    try:
        import chronicle_resolve as CR
    except Exception as e:
        return None, "chronicle_resolve could not be imported (%s)" % str(e)[:70]
    out = {}
    try:
        out["UNIQUE"] = CR.load_roster()
        out["SET"] = CR.load_set_roster()
    except Exception as e:
        return None, "a roster would not load (%s) - classification is UNKNOWN" % str(e)[:70]
    try:
        import json as _j
        doc = _j.load(io.open(os.path.join(HERE, "runeword_roster.json"), encoding="utf-8"))
        names = doc.get("names") or doc.get("runewords") or []
        if not names:
            return None, "runeword_roster.json holds no names - classification is UNKNOWN"
        out["RUNEWORD"] = {CR._norm(n): n for n in names}
    except Exception as e:
        return None, "the runeword roster would not load (%s)" % str(e)[:70]
    # ⚠⚠ AN EMPTY ROSTER IS UNKNOWN, NOT AN ANSWER — AND A SABOTAGE CAUGHT THIS LAW BEING VACUOUS.
    # The guard above leans on `load_roster` RAISING on an empty file, which it does today. But a
    # roster that arrives empty by any other route — a loader that stops raising, a truncated
    # file, a future third caller — would classify every name as NEITHER and make `tickable` read
    # a confident 0. That is the exact clean-zero this module was written to refuse, and relying
    # on somebody else's exception to prevent it is not a guard, it is a hope.
    # [[zero-needs-a-denominator]] [[feedback-suspect-the-instrument]]
    for k in ("UNIQUE", "SET", "RUNEWORD"):
        if not out.get(k):
            return None, ("the %s roster loaded EMPTY - classification is UNKNOWN, because an "
                          "empty roster would call every read name un-tickable" % k)
    return out, ""


def ledger_of(name, rost):
    """Which ledger this name could ever tick in. -> "UNIQUE"|"SET"|"RUNEWORD"|"NEITHER"|None"""
    if not rost:
        return None
    try:
        import chronicle_resolve as CR
    except Exception:
        return None
    if CR.canonical(name, rost.get("UNIQUE") or {}):
        return "UNIQUE"
    if CR.canonical(name, rost.get("SET") or {}):
        return "SET"
    if CR._norm(name) in (rost.get("RUNEWORD") or {}):
        return "RUNEWORD"
    # ⚠ AFTER the rosters, deliberately. If a fixture name were ever also a roster name, the
    # roster must win — this list exists to remove noise, never to hide a tickable item.
    if str(name).strip().lower() in FURNITURE:
        return "FURNITURE"
    return "NEITHER"


def referents_of(name, rost):
    """EVERY ledger this name matches, in roster order. -> list | None

    ⚠⚠ v3008 (#77) — `ledger_of` returns the FIRST match, and that first-match is itself where
    the ambiguity hides: Crescent Moon matches UNIQUE and the RUNEWORD hit is never reported, so
    nothing downstream could ever KNOW the name has three referents (two uniques share the name,
    plus the Shael+Um+Tir runeword). Two witnesses corroborate a NAME, not an ITEM — and a name
    with multiple referents cannot be auto-banked on evidence that does not distinguish them. The
    door refusing it was always right; this is what lets the door SAY SO. bible.html has ruled on
    this exact name in its own words ("the honest case: two different uniques carry that name").
    """
    if not rost:
        return None
    try:
        import chronicle_resolve as CR
    except Exception:
        return None
    out = []
    if CR.canonical(name, rost.get("UNIQUE") or {}):
        out.append("UNIQUE")
    if CR.canonical(name, rost.get("SET") or {}):
        out.append("SET")
    if CR._norm(name) in (rost.get("RUNEWORD") or {}):
        out.append("RUNEWORD")
    return out


def _containers(items):
    """Where the ITEM was, from the producer's per-name map. -> dict

    Returns `container` (only when every PLACED sighting agrees), `containers` (the full tally,
    so a disagreement is legible rather than averaged away), `placed`/`unplaced` as an explicit
    denominator pair, and `frameDisagreed` — how many sightings carry a frame `scene` that
    contradicts the item's own location. That last number is the one his 2026-09-12 ruling is
    about: it is the count of times the lane would have filed an inventory item as a stash item.
    """
    locs, placed, unplaced, dis = {}, 0, 0, 0
    for it in items or []:
        if not isinstance(it, dict):
            continue
        loc = it.get("loc")
        if not loc:
            unplaced += 1
            continue
        placed += 1
        locs[loc] = locs.get(loc, 0) + 1
        sc = str(it.get("scene") or "").strip().lower()
        if sc and sc != loc:
            dis += 1
    return {"container": (list(locs)[0] if len(locs) == 1 else None),
            "containers": locs, "placed": placed, "unplaced": unplaced,
            "frameDisagreed": dis}


def split(evidence_by_name=None, min_witnesses=None, conf_floor=None):
    """Which read names would AUTO-TALLY and which fall to the manual lane. -> dict

    ⛔ WRITES NOTHING. See the module docstring: banking releases footage for pruning.
    """
    try:
        import vault_retro as VR
    except Exception as e:
        return {"ok": False, "state": "UNKNOWN",
                "why": "vault_retro could not be imported (%s), so the split is UNKNOWN"
                       % str(e)[:70]}
    why = ""
    if evidence_by_name is None:
        evidence_by_name, why = evidence()
    if evidence_by_name is None:
        return {"ok": False, "state": "UNKNOWN", "why": why or "the journal could not be read"}

    rost, rwhy = rosters()
    # ⚠ GUARDED AT BOTH ENDS, DELIBERATELY. `rosters()` refuses to PRODUCE an empty roster, and
    # this refuses to CONSUME one. A sabotage that replaced `rosters` wholesale proved the
    # producer-side guard alone is not enough — any caller handing in empty dicts would classify
    # every name NEITHER and publish a confident `tickable: 0`.
    # [[feedback-fixtures-never-touch-live-data]] [[zero-needs-a-denominator]]
    if rost is not None and not all(rost.get(k) for k in ("UNIQUE", "SET", "RUNEWORD")):
        rost, rwhy = None, (rwhy or "a roster arrived EMPTY - classification is UNKNOWN")
    mw = VR.KEEP_MIN_WITNESSES if min_witnesses is None else min_witnesses
    cf = VR.KEEP_CONF_FLOOR if conf_floor is None else conf_floor
    auto, manual = [], []
    for nm in sorted(evidence_by_name):
        # the REAL gate, with the REAL bars — never a local reimplementation
        v = VR.gate(evidence_by_name[nm], cf, mw)
        row = {"name": nm, "witnesses": v.get("witnesses"), "sightings": v.get("sightings"),
               "bestConf": v.get("bestConf"), "why": v.get("why") or "",
               # ⚠ None (roster unreadable) is NOT "NEITHER". A name that cannot be classified is
               # unknown, and showing it as un-tickable would hide it from him for a reason that is
               # about my reader. [[unknown-stays-unknown]]
               "ledger": ledger_of(nm, rost),
               # ⚠ v2983 — WHERE THE ITEM ITSELF WAS, not which panel was on screen. See the
               # comment in evidence(): these are different questions and 66 of his 110 panel
               # sightings answer them differently. `container` is stated ONLY when every placed
               # sighting agrees; when they disagree it stays None and `containers` carries the
               # split, because "it moved" and "the reader is unsure" must not be flattened into a
               # confident single word. [[unknown-stays-unknown]]
               "referents": referents_of(nm, rost),
               **_containers(evidence_by_name[nm])}
        (auto if v.get("pass") else manual).append(row)
    return {"ok": True, "state": "MEASURED", "auto": auto, "manual": manual,
            "names": len(evidence_by_name), "minWitnesses": mw, "confFloor": cf,
            "why": why,
            # ⚠ the denominator travels with the verdict. A bare "3" is not a measurement.
            # [[zero-needs-a-denominator]]
            "rosterWhy": rwhy,
            "tickable": (None if rost is None else
                         len([r for r in auto + manual if r.get("ledger") not in
                              (None, "NEITHER", "FURNITURE")])),
            "furniture": (None if rost is None else
                          len([r for r in auto + manual if r.get("ledger") == "FURNITURE"])),
            "autoTickable": (None if rost is None else
                             len([r for r in auto if r.get("ledger") not in
                                  (None, "NEITHER", "FURNITURE")])),
            # ⚠ v3008 — THE DOOR'S VOICE. A name that clears the bar AND is on a roster AND has
            # MULTIPLE referents is HELD, not owed: auto-banking it would pick one of N referents
            # on evidence that cannot distinguish them. Held and owed are different answers and
            # the doctor must never report a correct hold as owed work. [[unknown-stays-unknown]]
            "autoHeld": (None if rost is None else
                         [{"name": r["name"], "referents": r.get("referents") or []}
                          for r in auto
                          if r.get("ledger") not in (None, "NEITHER", "FURNITURE")
                          and len(r.get("referents") or []) > 1]),
            "autoOwed": (None if rost is None else
                         [r["name"] for r in auto
                          if r.get("ledger") not in (None, "NEITHER", "FURNITURE")
                          and len(r.get("referents") or []) <= 1]),
            # ⚠ v2983 — THE HEADLINE HIS RULING EARNED. Not a ratio: the raw pair, so a reader
            # can see the denominator. [[zero-needs-a-denominator]]
            "frameItemDisagree": sum(r.get("frameDisagreed") or 0 for r in auto + manual),
            "placedSightings": sum(r.get("placed") or 0 for r in auto + manual),
            "unplacedSightings": sum(r.get("unplaced") or 0 for r in auto + manual),
            "lockedLaneNames": sorted(r["name"] for r in auto + manual
                                      if r.get("container") in ("inventory", "equipped")),
            "summary": ("%d of %d read name(s) clear %d witness(es); %d fall to the manual lane"
                        % (len(auto), len(evidence_by_name), mw, len(manual)))}


def report():
    s = split()
    if not s.get("ok"):
        print(u"UNKNOWN - %s" % s.get("why"))
        return 2
    print(u"READ NAMES -> WHERE THEY WOULD GO   (%s)" % s["summary"])
    print(u"  bars: %d witness(es), confidence >= %.2f" % (s["minWitnesses"], s["confFloor"]))
    print(u"\n  AUTO-TALLY (the existing vault_apply door):")
    for r in s["auto"] or [{"name": "(none)", "witnesses": 0, "sightings": 0}]:
        print(u"    %-34s %s witness(es), %s sighting(s)"
              % (r["name"], r.get("witnesses"), r.get("sightings")))
    print(u"\n  MANUAL LANE (his ruling: manual is the path for rares) - %d name(s):"
          % len(s["manual"]))
    for r in s["manual"][:12]:
        print(u"    %-34s %s witness(es)" % (r["name"], r.get("witnesses")))
    if len(s["manual"]) > 12:
        print(u"    ... and %d more" % (len(s["manual"]) - 12))
    return 0


if __name__ == "__main__":
    sys.exit(report())
