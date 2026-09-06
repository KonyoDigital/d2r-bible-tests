#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A15 clause 2 — ONE FUNNEL: *"they all flow down the same river together, through the same
feeding and routing system, for as long as they are indistinguishable."*

⚠⚠ THE CLAUSE SPLITS INTO TWO QUESTIONS AND ONLY ONE OF THEM HAS AN ANSWER TODAY. Answering the
easy one and calling the clause done is how a task gets marked shipped while the thing he asked for
is still unbuilt, so both are reported side by side and neither speaks for the other.

    THE LADDER   — is there ONE stage vocabulary, or does a lane have its own rungs?   ANSWERABLE
    THE PASSAGE  — did each reel actually FLOW down it, in order?                      MOSTLY NOT

MEASURED 2026-09-04, his 40 reels:

    STAGES declares 6 rungs — filmed · triaged · swept · banked · vault-done · releasable
    stageIdx <-> stage is a bijection on every reel; 0 reels at a stage the ladder does not know
    OCCUPIED: idx 2 `swept` 28 · idx 5 `releasable` 12.  FOUR RUNGS EMPTY.

⚠⚠ AND AN EMPTY RUNG IS NOT AN UNUSED ONE. `reel_story._stage_of` maps a reel's current HOLD TAG to
the rung it is stuck BEFORE — so `stage` is a BLOCKER, not a trajectory. "No reel sits at `banked`"
and "no reel ever passed `banked`" are opposite facts and the field cannot tell them apart. Reading
occupancy as a route is precisely the [[measured-true-read-wrong]] defect that opened A10.

⚠ SO THE PASSAGE IS ASKED OF THE DATED WAYPOINTS INSTEAD, and it is only PARTIAL: of the six rungs,
exactly two leave a timestamp behind — `retro_triage` (40 of 40 reels) and the seal store
`vault_swept` (15 of 40). The other four leave nothing dated, so for those rungs the order a reel
travelled in is not recorded anywhere and no probe can recover it. That is the honest state of
clause 2, and it names what would change it: a dated waypoint per rung.

    python3 tv/one_funnel.py
    python3 tv/one_funnel.py --json
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

#: Each rung, and WHERE THE NAME OF ITS STORE COMES FROM: the module that owns the store already
#: declares it, so this quotes the constant rather than restating the filename. `None` means no
#: store records that rung at all — a fact about the pipeline, not about a reel.
#:
#: ⚠⚠ THE FIRST CUT HARDCODED "retro_triage.json" AND "vault_swept.json", AND THE CONSEQUENCE WAS
#: REPRODUCED, not imagined: rename the store in its owning module and this probe does not follow,
#: so `triaged` — 40 of 40 reels covered — silently vanishes from the dated rungs while the verdict
#: stays PARTIAL and nothing looks wrong. A wrong answer wearing a measurement's clothes.
#: [[copy-drift]] §1: name ONE source, everything else quotes it.
#: A rung with no CACHE but a LIVE DECIDER. `reel_story`'s module docstring already names the
#: function that decides each stage; this quotes that mapping rather than restating it, for the
#: same reason WAYPOINT_SOURCES quotes the owning module's constant. The third field is the RULE
#: as reel_story states it, so a reader can check the claim without leaving this file.
#:
#: ⚠⚠ THE ABSENCE OF A STORE IS NOT THE ABSENCE OF A RECORD, and until v2725 this module said it
#: was. It printed "no store records this rung, so passing it leaves no trace" for these four,
#: while `plan()` answers for every reel on the shelf and `reel_story` maps all of them to a known
#: stage. Measured: onDisk 40, kept 40, stageKnown false for ZERO. The state was observable the
#: whole time; what is missing is the DATE of passage, not the fact of it.
#: [[unknown-stays-unknown]] — and the sting is that this module cites that law five times.
DERIVED_SOURCES = {
    "filmed":     ("reel_retention", "plan", "the reel directory exists (onDisk)"),
    "banked":     ("reel_retention", "plan", "tag != rows-not-banked"),
    "vault-done": ("reel_retention", "plan", "tag != vault-owes"),
    "releasable": ("reel_retention", "plan", "tag == eligible"),
}

WAYPOINT_SOURCES = {
    "filmed":     None,
    "triaged":    ("retro_triage", "STORE"),
    "swept":      ("frame_authority", "SEAL_STORE"),
    "banked":     None,
    "vault-done": None,
    "releasable": None,
}


def _store_of(rung):
    """The store filename for a rung, asked of the module that owns it. -> (name, why)

    ⚠ A store whose owner will not import, or which stopped declaring its constant, returns None
    WITH A REASON — never a guessed filename. A guess here would read a file that may not be the
    store and report its coverage as the rung's.
    """
    src = WAYPOINT_SOURCES.get(rung)
    if not src:
        return None, "no store records this rung, so passing it leaves no trace"
    mod, const = src
    try:
        m = __import__(mod)
    except Exception as e:
        return None, "%s would not import, so its store cannot be named (%s)" % (mod, str(e)[:50])
    name = getattr(m, const, None)
    if not name:
        return None, "%s no longer declares %s, so its store cannot be named" % (mod, const)
    return str(name), ""


def waypoints():
    """The live rung -> store-filename view. -> dict

    ⚠⚠ REG-537 — THIS WAS A FROZEN DICT, AND IT RE-CREATED THE DEFECT REG-534 HAD JUST FIXED, ONE
    LINE BELOW THE FIX. It read `WAYPOINTS = {rung: _store_of(rung)[0] for rung in ...}`, evaluated
    ONCE at import, so the moment an owner renamed its store the snapshot disagreed with the
    resolver three lines above it. Reproduced:

        _store_of('triaged')  -> retro_triage_RENAMED.json    (follows the owner)
        WAYPOINTS['triaged']  -> retro_triage.json            (frozen at import — STALE)

    ⚠ And its own comment claimed it existed "for readers and for the guard that pins it against
    the owning modules" — a grep found **no reader anywhere**, and the guard pins `_store_of`, not
    this. A stale copy maintained for a consumer that does not exist. [[plumbing-with-no-tap]]
    [[copy-drift]] §1. A function cannot go stale, so it is one.
    """
    return {rung: _store_of(rung)[0] for rung in WAYPOINT_SOURCES}


def _ladder():
    """-> (rungs, why). The stage vocabulary, asked of the module that owns it."""
    try:
        import reel_story as RS
        st = tuple(getattr(RS, "STAGES", ()) or ())
        return st, ("" if st else "reel_story declares no STAGES")
    except Exception as e:
        return (), "reel_story would not import (%s)" % str(e)[:80]


def _rows():
    try:
        import reel_story as RS
        st = RS.story()
        return (st.get("reels") or []) if isinstance(st, dict) else [], ""
    except Exception as e:
        return [], "reel_story would not answer (%s)" % str(e)[:80]


def _decided_count():
    """How many reels the live deciders answer for. -> (decided, total, why)

    ⚠ A decider that will not run returns (None, None, reason) — UNKNOWN, never 0. The store path
    six lines below already learned this the hard way (REG-559: an unreadable store produced an
    empty `dated` and a confident finding over evidence nobody gathered). A derived rung is
    exactly as capable of that mistake, so it refuses the same way.
    """
    try:
        import reel_story as RS
        st = RS.story()
    except Exception as e:
        return None, None, "reel_story would not answer (%s)" % str(e)[:70]
    if not isinstance(st, dict):
        return None, None, ("reel_story answered with %s, not a mapping — there is no shelf here "
                            "to count" % type(st).__name__)
    reels = st.get("reels")
    if not reels:
        return None, None, "reel_story returned no reels, so nothing was decided either way"
    # ⚠⚠ A TRUTHY NON-SEQUENCE IS NOT A SHELF. Measured: {"reels": "abcdefg"} answered
    # (0, 7) — seven "reels" that are the characters of a string, none of them decided. That is
    # the strongest possible finding, manufactured by iterating whatever arrived.
    if not isinstance(reels, (list, tuple)):
        return None, None, ("reel_story's `reels` is %s, not a sequence — counting it would "
                            "iterate whatever it happens to be" % type(reels).__name__)
    # ⚠⚠ AND THE STAGE MUST BE ONE THE LADDER DECLARES. `funnel()`'s ladder loop counts a
    # reel at an unknown stage as `unknownStage` and this counted the same reel as DECIDED, so the
    # two readings of one shelf disagreed about how many reels are placed and the observability
    # verdict rested on the more generous of the two. `is True` rather than truthy for the same
    # reason `_row_fault` refuses a bool count: a stray string must not pass as a declaration.
    # [[feedback-contradiction-is-the-finding]]
    rungs, _lwhy = _ladder()
    decided = sum(1 for r in reels
                  if isinstance(r, dict) and r.get("stageKnown") is True and r.get("stage")
                  and (not rungs or r.get("stage") in rungs))
    return decided, len(reels), ""


def _waypoint_cover(sids):
    """For each rung with a store, how many of these reels it has a dated row for. -> dict"""
    out = {}
    for rung in WAYPOINT_SOURCES:
        store, swhy = _store_of(rung)
        if not store:
            # ⚠ NOT CACHED IS NOT NOT KNOWN. Ask whether a live decider owns this rung before
            # reporting it as traceless — the sentence this used to print was measured FALSE for
            # all four storeless rungs on 2026-09-06.
            src = DERIVED_SOURCES.get(rung)
            if not src:
                out[rung] = {"store": None, "covered": None, "derivedBy": None,
                             "decided": None, "why": swhy}
                continue
            mod, fname, rule = src
            dec, tot, dwhy = _decided_count()
            out[rung] = {
                "store": None, "covered": None,
                "derivedBy": "%s.%s()" % (mod, fname), "rule": rule,
                "decided": dec, "decidedOf": tot,
                "why": (dwhy or
                        ("no store CACHES this rung, but %s.%s() decides it live (%s) and answers "
                         "for %d of %d reel(s). The state is observable; what is absent is the "
                         "DATE of passage, not the fact of it."
                         % (mod, fname, rule, dec, tot))),
            }
            continue
        p = os.path.join(HERE, store)
        try:
            blob = json.loads(io.open(p, encoding="utf-8").read())
        except Exception as e:
            # ⚠ UNREADABLE IS NOT ZERO COVERAGE. A store we could not open tells us nothing about
            # how many reels it holds. [[unknown-stays-unknown]]
            # ⚠ AND IT NAMES THE STORE. The first cut printed only str(e)[:60], which on a real
            # path cut off mid-directory — "/Users/konyo/d2r_bible" — hiding the one word that
            # would diagnose it. The filename comes first now, then as much of the error as fits.
            out[rung] = {"store": store, "covered": None,
                         "why": "%s would not read (%s)" % (store, str(e)[-70:])}
            continue
        if not isinstance(blob, dict):
            out[rung] = {"store": store, "covered": None,
                         "why": "the store is %s, not an object" % type(blob).__name__}
            continue
        # ⚠⚠ A FRACTION OVER ZERO REELS IS NOT A MEASUREMENT OF THIS STORE. With `sids`
        # empty the sum is 0 for every store, `_observability` reads that as `dark`, and the
        # passage reads UNRECORDED — "no rung leaves a dated waypoint", asserted about his
        # pipeline over nothing examined. Reachable whenever every row on the shelf is nameless:
        # `funnel()` refuses an EMPTY shelf, never a shelf whose rows carry no reel name.
        # [[zero-needs-a-denominator]] [[unknown-stays-unknown]]
        if not sids:
            out[rung] = {"store": store, "covered": None,
                         "why": "%s was readable, but no reel was named to look up — 0 of 0 is a "
                                "fraction with no denominator, not coverage of zero" % store}
            continue
        n = sum(1 for s in sids if s in blob or ("reel_" + s) in blob)
        out[rung] = {"store": store, "covered": n,
                     "why": "%d of %d reel(s) have a dated row here" % (n, len(sids))}
    return out


def _count(v):
    """A figure that is really a COUNT, or None because it is not one. -> int|None

    ⚠⚠ THREE SHAPES ARRIVE HERE WEARING A COUNT'S CLOTHES, and all three were measured
    reading as measurements on the shipped bytes:

        True   `bool` is a subclass of `int`, so `True > 0` held and a store reporting
               `covered=True` was read as "one reel covered" — OBSERVED. The same shape
               `self_arming._row_fault` already refuses on its own rows.
        -1     an impossible coverage, read as "answers for nobody" — a finding about his
               pipeline manufactured from an instrument fault.
        "3"    a string count, which would compare and sort and never be a number.

    None means NOT A MEASUREMENT, which every caller here turns into UNKNOWN rather than a
    fraction. [[unknown-stays-unknown]]
    """
    if isinstance(v, bool) or not isinstance(v, int) or v < 0:
        return None
    return v


def _observability(cover):
    """Can every rung's state be established for every reel RIGHT NOW? -> dict

    A rung counts as observable if a store holds rows for it OR a live decider answers for it.
    ⚠ UNKNOWN PROPAGATES. One rung nobody can read makes the whole verdict UNKNOWN rather than
    dragging a fraction down — a rung that could not be measured is not a rung measured as absent.
    """
    # ⚠⚠ A COVER THAT IS NOT A MAPPING HAS NO VERDICT, AND THIS RAISED INSTEAD OF SAYING SO.
    # Measured: `_observability(["filmed", "triaged"])` -> AttributeError. A caller that catches
    # nothing loses the whole funnel; a caller that catches everything records a crash as a
    # reading. UNKNOWN is the honest answer and it is the one this module gives everywhere else.
    if not isinstance(cover, dict):
        return {"state": "UNKNOWN", "seen": 0, "rungCount": 0, "unknown": [], "dark": [],
                "why": "the cover is %s, not a mapping of rung -> reading, so no rung was "
                       "examined" % type(cover).__name__}
    total = len(cover)
    # ⚠⚠ AN EMPTY COVER MAP IS NOT A CLEAN BILL OF HEALTH, and this function shipped saying it was
    # for exactly as long as it took to write the attack table below. With `cover == {}` the loop
    # never runs, `seen == total` holds at 0 == 0, and the verdict read OBSERVED with the sentence
    # "every one of the 0 rung(s) can be established". A fraction over nothing examined is the
    # [[zero-needs-a-denominator]] shape — the same law this module's own tests cite — and it was
    # found by designing a sabotage for it, not by reading the code back.
    if not total:
        return {"state": "UNKNOWN", "seen": 0, "rungCount": 0, "unknown": [], "dark": [],
                "why": "no rung was examined, so nothing is observable and nothing is dark either"}
    seen, unknown, dark = 0, [], []
    for rung, v in cover.items():
        # ⚠ A RUNG WHOSE READING IS NOT A MAPPING IS UNMEASURED, NOT DARK. `v.get` raised here.
        if not isinstance(v, dict):
            unknown.append(rung)
            continue
        if v.get("store"):
            c = _count(v.get("covered"))
            if c is None:
                unknown.append(rung)
            elif c > 0:
                seen += 1
            else:
                dark.append(rung)
        elif v.get("derivedBy"):
            c = _count(v.get("decided"))
            tot = _count(v.get("decidedOf"))
            # more reels decided than exist is an instrument fault, not a strong result — the
            # same refusal `self_arming.bank()` makes for k > n.
            if c is None or (tot is not None and c > tot):
                unknown.append(rung)
            elif c > 0:
                seen += 1
            else:
                dark.append(rung)
        else:
            dark.append(rung)
    if unknown:
        state = "UNKNOWN"
        why = ("%d of %d rung(s) could not be measured (%s), so no honest fraction exists"
               % (len(unknown), total, ", ".join(sorted(unknown))))
    elif seen == total:
        state = "OBSERVED"
        why = ("every one of the %d rung(s) can be established for the reels on the shelf — %d by "
               "a dated store, %d by a live decider. This says NOTHING about whether the passage "
               "was DATED; read `passage` for that." % (total, seen - _derived_seen(cover),
                                                        _derived_seen(cover)))
    else:
        state = "PARTIAL"
        why = ("%d of %d rung(s) can be established; %s answer for nobody"
               % (seen, total, ", ".join(sorted(dark))))
    return {"state": state, "seen": seen, "rungCount": total,
            "unknown": sorted(unknown), "dark": sorted(dark), "why": why}


def _derived_seen(cover):
    return sum(1 for v in cover.values()
               if not v.get("store") and v.get("derivedBy") and (v.get("decided") or 0) > 0)


def funnel():
    """-> {"ok", "ladder", "passage", "rungs", "occupancy", "why"}

    Two independent readings, never merged:
      ladder  — ONE_LADDER / SPLIT_LADDER / UNKNOWN
      passage — RECORDED / PARTIAL / UNRECORDED / UNKNOWN
    """
    # ⚠⚠ REG-546 — EVERY RETURN CARRIES THE SAME KEYS. These two dropped SEVEN of them —
    # collisions, datedRungs, occupancy, rungCount, unknownStage, walked, waypoints — so a caller
    # reading any one broke on exactly the paths that mean NOTHING WAS ESTABLISHED. Caught by the
    # cross-probe SHAPE law, which found this and one in one_start_point on its first run.
    def _unknown(w, rungs=()):
        return {"ok": False, "state": "UNKNOWN", "ladder": "UNKNOWN", "passage": "UNKNOWN",
                "rungs": list(rungs), "collisions": [], "unknownStage": 0, "occupancy": {},
                "waypoints": {}, "walked": 0, "datedRungs": [], "rungCount": len(rungs),
                "unreadableRungs": [], "emptyStoreRungs": [], "namelessRows": 0,
                # REG-546's law applies to every key this function can return, including the ones
                # added after it was written: a caller reading `observability` must not break on
                # exactly the paths that mean NOTHING WAS ESTABLISHED.
                "observability": {"state": "UNKNOWN", "seen": 0, "rungCount": len(rungs),
                                  "unknown": [], "dark": [],
                                  "why": "nothing was established, so nothing is observable"},
                "why": w}

    rungs, lwhy = _ladder()
    rows, rwhy = _rows()
    if not rungs:
        return _unknown("UNKNOWN, not a split ladder — %s" % (lwhy or "no ladder was found"))
    if not rows:
        return _unknown("UNKNOWN, not an empty shelf — %s"
                        % (rwhy or "no reel reached this probe and nothing said why"), rungs)

    by_idx, by_stage, unknown, occupancy = {}, {}, 0, {}
    for r in rows:
        if not isinstance(r, dict):
            continue
        stage, idx = r.get("stage"), r.get("stageIdx")
        if not r.get("stageKnown", True) or stage not in rungs:
            unknown += 1
            continue
        by_idx.setdefault(idx, set()).add(stage)
        by_stage.setdefault(stage, set()).add(idx)
        occupancy[stage] = occupancy.get(stage, 0) + 1
    # A rung naming two stages, or a stage sitting at two rungs, is two ladders sharing a vocabulary
    collisions = ([{"index": i, "stages": sorted(s)} for i, s in by_idx.items() if len(s) > 1]
                  + [{"stage": s, "indexes": sorted(i)} for s, i in by_stage.items() if len(i) > 1])
    ladder = "ONE_LADDER" if (not collisions and not unknown) else "SPLIT_LADDER"

    # ⚠⚠ REG-559 — A PHANTOM SESSION ID. This added `""` to `sids` for any row naming no reel —
    # a non-dict, a missing `reel` key, a bare `"reel_"` — and handed it to `_waypoint_cover`,
    # which then asked every store whether it held a row for the empty string. The SAME class as
    # REG-550's phantom reel in the printer, in a different module, found by a cold review of
    # these bytes rather than by my sweep of that one. **A sweep of a class is only as wide as the
    # modules you looked in**, and I had looked in one.
    sids, nameless = set(), 0
    for r in rows:
        # ⚠⚠ `(r or {})` DOES NOT MAKE A NON-MAPPING SAFE — `"x" or {}` is `"x"`, and this
        # raised AttributeError on any row that is not a dict. The ladder loop above defends
        # against precisely that shape and continues past it, so one module both expected and
        # forbade the same row and only one of the two loops said so. A row nobody can read has
        # no reel name, which is what `nameless` already counts. [[the-unjoined-end]]
        if not isinstance(r, dict):
            nameless += 1
            continue
        nm = str(r.get("reel") or "").strip()
        sid = nm[len("reel_"):] if nm.startswith("reel_") else nm
        if not sid:
            nameless += 1
            continue
        sids.add(sid)
    cover = _waypoint_cover(sids)
    # ⚠ SAME `_count` RULE AS THE OBSERVABILITY VERDICT: `covered=True` must not date a rung.
    # ⚠⚠ AND ONLY RUNGS THE LADDER DECLARES MAY COUNT TOWARD IT. `len(dated) >= len(rungs)`
    # weighs a count from WAYPOINT_SOURCES against a count from reel_story.STAGES; measured with
    # six dated rungs the ladder does not name, the passage read RECORDED — the strongest verdict
    # available, over rungs nobody measured. The two vocabularies are identical today, which is
    # exactly when a drift guard is cheap. [[copy-drift]]
    dated = [k for k, v in cover.items()
             if k in rungs and isinstance(v, dict) and _count(v.get("covered"))]
    offLadder = sorted(k for k in cover if k not in rungs)
    unwatched = sorted(r for r in rungs if r not in cover)
    # ⚠⚠ REG-555 — UNRECORDED IS A CLAIM ABOUT THE PIPELINE, AND IT WAS BEING MADE OVER STORES
    # NOBODY COULD READ. Measured with both waypoint stores pointed at a directory: `dated` came
    # back empty and the passage read UNRECORDED — *"no rung leaves a dated waypoint"* — which is a
    # finding about his pipeline, asserted over evidence that was never gathered. "No store records
    # this rung" and "the store could not be read" are opposite facts and both produced an empty
    # `dated`. A rung whose store is UNREADABLE makes the passage UNKNOWN, not UNRECORDED.
    # [[unknown-stays-unknown]]
    unreadable = sorted(k for k, v in cover.items()
                        if v.get("store") and v.get("covered") is None)
    # ⚠⚠ REG-559 — THREE FACTS, TWO LISTS. A rung's store can be ABSENT (nothing records it),
    # UNREADABLE (it exists and would not open), or READ AND EMPTY (it opened and holds a dated
    # row for none of these reels). The first two had a home and the third had none: `covered == 0`
    # fell out of `dated` AND out of `unreadable`, so a rung that WAS checked and found empty read
    # exactly like a rung nobody records. Different facts about his pipeline.
    empty_stores = sorted(k for k, v in cover.items() if v.get("covered") == 0)
    if unreadable:
        passage = "UNKNOWN"
    elif offLadder or unwatched:
        # the two vocabularies have drifted, so no fraction of "rungs dated" is about the ladder
        passage = "UNKNOWN"
    elif len(dated) >= len(rungs):
        passage = "RECORDED"
    elif dated:
        passage = "PARTIAL"
    else:
        passage = "UNRECORDED"

    return {
        "ok": True, "ladder": ladder, "passage": passage,
        "rungs": list(rungs), "collisions": collisions, "unknownStage": unknown,
        "occupancy": occupancy, "waypoints": cover, "walked": len(rows),
        "datedRungs": sorted(dated), "rungCount": len(rungs), "unreadableRungs": unreadable,
        "emptyStoreRungs": empty_stores, "namelessRows": nameless,
        # ⚠⚠ A SECOND, INDEPENDENT READING — deliberately NOT folded into `passage`.
        # `passage` answers "is a reel's HISTORY through the rungs recorded?" and the answer is
        # still PARTIAL: two rungs keep a dated row and four do not. `observability` answers a
        # different question — "can every rung's state be established for every reel, right now?"
        # Merging them would turn a real gap into a green number, which is precisely the move
        # [[t155]] warned against when the evidence pointed the other way. Publish both.
        "observability": _observability(cover),
        # ⚠⚠ REG-558 — THE PREFIX BOUND INSIDE THE TERNARY'S TRUE BRANCH. `+` binds tighter than
        # the conditional expression, so `prefix + A if c else B` parses as `(prefix + A) if c else
        # B` — and the unreadable-stores warning reached ONLY the ONE_LADDER text. Measured: with
        # both stores unreadable AND a stage collision, `passage` said UNKNOWN and
        # `unreadableRungs` held two entries while the prose said nothing about either. The
        # numbers were right and the sentence a reader sees was silent. Parenthesised so the
        # prefix applies to both branches.
        "why": (("\u26a0 %d rung(s) have a store that COULD NOT BE READ (%s), so the passage is "
                 "UNKNOWN — nothing was established, which is a different fact from no rung "
                 "leaving a waypoint. " % (len(unreadable), ", ".join(unreadable)))
                if unreadable else "")
               + (("ONE stage vocabulary across %d reel(s) — %d rung(s), no rung naming two stages "
                "and no stage at two rungs. ⚠ BUT THE PASSAGE IS %s: %d of %d rung(s) leave a "
                "dated waypoint (%s), so for the rest the order a reel travelled in is recorded "
                "NOWHERE. ⚠ And occupancy is not a route: `stage` is the rung a reel is stuck "
                "BEFORE, so an empty rung means nobody is stuck there — never that nobody passed."
                % (len(rows), len(rungs), passage, len(dated), len(rungs),
                   ", ".join(sorted(dated)) or "none")) if ladder == "ONE_LADDER" else
               ("SPLIT LADDER — %d collision(s) and %d reel(s) at a stage the ladder does not "
                "know. A lane with its own rungs is a lane with its own routing system, which is "
                "what A15 forbids." % (len(collisions), unknown))),
    }


def main(argv):
    r = funnel()
    if "--json" in argv:
        print(json.dumps(r, indent=2, sort_keys=True, default=list))
        return 0
    print("\nA15 clause 2 — ONE FUNNEL: do they all flow down the same river?\n")
    if not r["ok"]:
        print("  %s\n" % r["why"])
        return 0
    print("  THE LADDER   %s" % r["ladder"])
    print("  THE PASSAGE  %s   (%d of %d rungs leave a dated waypoint)"
          % (r["passage"], len(r["datedRungs"]), r["rungCount"]))
    print()
    for rung in r["rungs"]:
        w = r["waypoints"].get(rung) or {}
        occ = r["occupancy"].get(rung, 0)
        print("     %-12s occupied %2d   waypoint: %s" % (rung, occ, w.get("why", "")))
    print()
    print("  ⚠ OCCUPANCY IS NOT A ROUTE. `stage` is the rung a reel is stuck BEFORE, so an empty")
    print("    rung means nobody is stuck there — a different fact from nobody passing through.")
    print("\n  %s\n" % r["why"])
    return 0


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
