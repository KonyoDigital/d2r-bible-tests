#!/usr/bin/env python3
"""THE HEART OF THE CONSOLE — one vocabulary, everything that runs, and a score on all of it.

Konyo, A16: *"make sure watchdog and corrobator eagle eye and doctor (the Heart of the Console) is
what we called it and wilson score it all!! connect it all to the HEART OF THE CONSOLE"* — and
later, 2026-09-02: *"the heart should be wilson score too, not just doctor / eagle eye / watchdog /
corroborator — wilson score embedded in it too."*

═══ THE TWO LIMITS A16 SAYS MUST BE FIXED FIRST, OR THE HEART SUPERVISES AIR ═══════════════════

**1. IT CAN ONLY SUPERVISE WHAT REPORTS IN ONE VOCABULARY.** Four organs speaking four dialects is
four dashboards, not a heart. So every vessel below answers the SAME four questions in the SAME
words, whatever produced it.

**2. IT CAN ONLY SUPERVISE WHAT IT KNOWS EXISTS — AND IT DID NOT.** Measured 2026-09-02 by
`lane_census`: **30 thread targets · 11 supervised · 8 UNWATCHED loops · 2 unclassifiable.** Two of
those eight unwatched loops had a real defect found the same day — `_kai_closer_loop` was leaking a
defunct child per reel, and `_orphan_exit_loop` was absent from `BLUEPRINT.md` entirely. That is not
a coincidence; it is the argument for this file.

⚠ A16 also says: *"The 21 / 11 that stood here was from a classifier later proven wrong; do not
quote it."* Nothing here hardcodes a census figure — it ASKS `lane_census`, every time.

═══ THE VOCABULARY — four words, and they are four on purpose ══════════════════════════════════

    FLOWING   it runs, something watches it, AND a sabotage has proven the watcher can refuse
    WATCHED   it runs and something watches it, but nothing has ever tried to break the watcher
    DARK      it RUNS AND NOTHING WATCHES IT. Not broken — unseen, which reads as fine and is worse
    UNKNOWN   it could not be classified, and that is not the same as harmless

⚠ WATCHED IS NOT A FAILURE AND MUST NOT LOOK LIKE ONE. It means work owed. A heart that painted its
own newest vessels red would be ignored inside a week, which is [[heart-first]] §5's warning about
a score that turns amber at its newest checks.

⚠ AND `DARK` IS NOT `UNKNOWN`. Dark means measured-and-nothing-watches; unknown means the census
could not tell. Collapsing them is the same lie as collapsing 0 with None.

═══ WHAT THIS FILE WILL NOT DO ═════════════════════════════════════════════════════════════════

It DERIVES and REPORTS. It never draws, never caches a picture, never writes. A hand-maintained
diagram is a map that drifts from the territory, and this repo paid for exactly that on 2026-09-02
when `BLUEPRINT.md` — a GENERATED artifact — went stale and a gate graded the last build. The heart
is recomputed from the census, the health rows and the lock ledger on every read, so there is no
stored copy to go stale.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

FLOWING = "FLOWING"
WATCHED = "WATCHED"
DARK = "DARK"
UNKNOWN = "UNKNOWN"

#: a lane whose census kind is one of these is NOT a vessel, and saying so is deliberate.
#: lane_census itself marks them "a roster entry would be a lie" — they are one-shot work kicked
#: off by something else and they inherit their caller's vessel. Giving each its own would make the
#: roster claim more runs without you than there are.
NOT_A_VESSEL = ("TASK",)


def _census():
    """-> (rows, why). rows is None when the census could not be taken, which is UNKNOWN."""
    try:
        import lane_census as LC
    except Exception as e:
        return None, "lane_census will not import — %s" % str(e)[:90]
    fn = getattr(LC, "census", None)
    if not callable(fn):
        # ⚠ REFUSE, DO NOT GUESS AT A REPLACEMENT. If census() is gone the shape has changed, and a
        # parser that shrugs and tries the next likely name would silently reclassify every lane.
        return None, "lane_census no longer exposes census() — the shape changed, so this is UNKNOWN"
    try:
        return fn(), ""
    except Exception as e:
        return None, "lane_census.census() raised — %s" % str(e)[:70]


def _health_rows():
    """The organ rows — eagle/doctor/watchdog/corroborator all land here. -> (list, why)"""
    try:
        import health_engine as HE
    except Exception as e:
        return [], "health_engine will not import — %s" % str(e)[:90]
    try:
        rep = HE.report()
    except Exception as e:
        return [], "health_engine.report() raised — %s" % str(e)[:70]
    if isinstance(rep, dict):
        return list(rep.get("rows") or []), ""
    return list(rep or []), ""


def _locks():
    """The self-arming locks — the surfaces that ACT. -> (list, why)"""
    try:
        import self_arming as SA
        rep = SA.report()
    except Exception as e:
        return [], "the locks could not be read — %s" % str(e)[:80]
    if not rep.get("ok"):
        return [], rep.get("why", "")
    return list(rep.get("locks") or []), ""


def vessels():
    """Everything that runs on its own, in ONE vocabulary. -> dict

    ⚠ THE COUNTS ARE DERIVED, NEVER TYPED. A16 explicitly warns that a hardcoded census figure in
    this file went wrong once already and must not be quoted; so the census is ASKED on every call
    and an unavailable census produces UNKNOWN rather than a remembered number.
    """
    rows, why = _census()
    if rows is None:
        return {"ok": False, "why": why, "vessels": [],
                "counts": {FLOWING: None, WATCHED: None, DARK: None, UNKNOWN: None},
                "notVessels": None}

    organs, organ_why = _health_rows()
    locks, lock_why = _locks()

    # a vessel is FLOWING only if some organ row about it carries a real score. `score` is None
    # when nobody has tested it and 0.0 when it was tested and never refused — those must not
    # collapse, so `proven` asks for a number ABOVE zero rather than for truthiness.
    scored = {}
    for r in organs:
        if not isinstance(r, dict):
            continue
        s = r.get("score")
        scored[str(r.get("id") or "")] = s if isinstance(s, (int, float)) else None

    # ⚠⚠ CAN A VESSEL EVER BECOME FLOWING? ASK BEFORE TELLING HIM WORK IS OWED.
    # `scored` is keyed on the organ rows' OWN ids — lanes, readers, selfArming, board_join — and
    # `watcher` is a LANE name, tvd-eagle-watch and its siblings. The two vocabularies are
    # DISJOINT, so `scored.get(watcher)` returns None for every vessel that exists and the FLOWING
    # branch is unreachable with real data. Measured: score every organ 1.0 and the census still
    # reads FLOWING 0; score the WATCHER names instead and 11 turn FLOWING at once.
    #
    # The sentence that shipped under that was "watched, but nothing has ever tried to break the
    # watcher — that is work owed, not a fault". It is FALSE in the way that costs most: it names
    # a job which, if someone did it, would change nothing. Nobody-has-tested-it and
    # nothing-can-record-a-test-here are different facts, exactly as they were for vault.forget,
    # and a panel that cannot tell them apart sends him to do work that cannot land.
    # [[unknown-stays-unknown]] [[the-unjoined-end]]
    _watchers = set()
    for row in rows:
        _n, _k, _w = _read_census_row(row)
        if _w:
            _watchers.add(_w)
    _scorable = bool(_watchers & set(k for k, v in scored.items() if v is not None))

    out, not_vessels = [], 0
    for row in rows:
        name, kind, watcher = _read_census_row(row)
        if kind in NOT_A_VESSEL:
            not_vessels += 1
            continue
        if kind not in ("LOOP",):
            out.append({"name": name, "kind": kind, "state": UNKNOWN,
                        "why": "the census could not classify this, which is not the same as "
                               "harmless — it may run forever and nothing would know"})
            continue
        if not watcher:
            out.append({"name": name, "kind": kind, "state": DARK, "watcher": None,
                        "why": "it runs and NOTHING watches it. Not broken — unseen, which reads "
                               "as fine and is worse"})
            continue
        sc = scored.get(watcher)
        if isinstance(sc, (int, float)) and sc > 0:
            out.append({"name": name, "kind": kind, "state": FLOWING, "watcher": watcher,
                        "score": round(float(sc), 4),
                        "why": "watched, and a sabotage has proven the watcher can refuse"})
        else:
            out.append({"name": name, "kind": kind, "state": WATCHED, "watcher": watcher,
                        "score": None,
                        "scorable": _scorable,
                        "why": ("watched, but nothing has ever tried to break the watcher — that "
                                "is work owed, not a fault")
                               if _scorable else
                               ("watched, and NOTHING CAN SCORE THIS WATCHER YET. No organ "
                                "publishes a score under a lane name, so no amount of sabotage "
                                "would move this row — that is a missing scorer, not work owed "
                                "by anyone")})

    counts = {FLOWING: 0, WATCHED: 0, DARK: 0, UNKNOWN: 0}
    for v in out:
        counts[v["state"]] = counts.get(v["state"], 0) + 1

    return {
        "ok": True,
        "vessels": sorted(out, key=lambda v: (v["state"] != DARK, v["name"])),
        "counts": counts,
        "notVessels": not_vessels,
        "locks": locks,
        "why": "; ".join([w for w in (organ_why, lock_why) if w]),
    }


def _read_census_row(row):
    """One census row. -> (name, kind, watcher|None)

    The shape is lane_census.census()'s own: {fn, kind, lane, supervised, via}. It is read
    LITERALLY rather than sniffed — a tolerant parser over another module's output is how a shape
    change silently reclassifies every lane, and this file's whole job is knowing what exists.
    A row that is not that shape becomes UNKNOWN, which is visible.
    """
    if not isinstance(row, dict) or "fn" not in row:
        return str(row)[:40], "UNKNOWN", None
    name = str(row.get("fn") or "?")
    kind = str(row.get("kind") or "UNKNOWN").upper()
    # `supervised` is the census's own verdict and `lane` is the roster name it was registered
    # under. A lane that is supervised but carries no roster name would be a contradiction, so it
    # is reported as UNKNOWN rather than quietly counted either way.
    if row.get("supervised"):
        return name, kind, (str(row.get("lane")) if row.get("lane") else None)
    return name, kind, None


def main(argv):
    rep = vessels()
    if not rep.get("ok"):
        print("THE HEART CANNOT BE READ — %s" % rep.get("why"))
        return 0            # a report is not a verdict
    c = rep["counts"]
    print("THE HEART — %d flowing · %d watched · %d DARK · %d unknown   (%d tasks are not vessels)"
          % (c[FLOWING], c[WATCHED], c[DARK], c[UNKNOWN], rep["notVessels"]))
    for v in rep["vessels"]:
        print("  %-8s %-24s %s" % (v["state"], v["name"], (v.get("why") or "")[:78]))
    return 0


if __name__ == "__main__":
    try:
        import console_safe as _cs
        _cs.enable()
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
