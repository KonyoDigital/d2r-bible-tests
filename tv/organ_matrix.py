#!/usr/bin/env python3
"""A3 — WHICH SURFACES HAVE WHICH ORGANS, MEASURED, WITH THE HOLES LEFT AS HOLES.

His ask, over a table that was mostly empty: *"fix those gaps and anywhere else.. make it unified
and logical and coded properly with watchdogged and eagle eyed and doctor and corraborotror"* —
`surfaces registry` empty across every column, `stash_eye grid` empty, `enlarge` empty, `OCR worker`
present in exactly one. **Every surface gets the same four organs, or it is honestly marked as not
having them.**

⚠⚠ THIS FILE DOES NOT FILL THE TABLE IN. It measures it. A matrix that reports coverage it cannot
demonstrate is worse than the empty one he was shown, because the empty one at least told the
truth. Every cell here is one of:

    COVERED    the organ's own output NAMES this surface — checked, not assumed
    ABSENT     the organ runs and does not name it
    UNKNOWN    the organ could not be asked at all (no report, would not import, raised)

⚠ UNKNOWN IS NOT ABSENT. Two of the four organs have no callable report on this tree —
console_doctor exposes none and there is no `eagle` module — so their columns are UNKNOWN
everywhere rather than empty, and the difference is the whole point. An organ nobody can ask has
not been shown to miss anything; it has not been shown to do anything either.
[[unknown-stays-unknown]] [[the-unjoined-end]]
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

COVERED, ABSENT, UNKNOWN, MISNAMED = "COVERED", "ABSENT", "UNKNOWN", "MISNAMED"

#: The four organs, and how to ask each one what it covers. `None` where nothing can be asked —
#: recorded as an absence of an INSTRUMENT, never as an absence of coverage.
ORGANS = ("eagle", "watchdog", "doctor", "corroborator")


#: ⚠ "key" BELONGS HERE AND ITS ABSENCE MADE A LIVE ORGAN LOOK DEAD. The route rows identify
#: themselves with `key`, not `id`/`name`/`route`, so the corroborator extracted nothing and this
#: file reported "no route set answered" about three modules that had answered all day. A reader
#: would have concluded the corroborator was broken; the extractor was. Suspect the instrument.
def _names_from(rows, keys=("id", "key", "lane", "route", "name", "surface", "lock", "target")):
    out = set()
    for r in (rows or []):
        if isinstance(r, dict):
            for k in keys:
                v = r.get(k)
                if isinstance(v, str) and v:
                    out.add(v)
        elif isinstance(r, str):
            out.add(r)
    return out


def _ask(mod_name, attr, extract):
    """-> (set_of_names, why_unknown). An organ that cannot be asked yields (None, reason)."""
    try:
        mod = __import__(mod_name)
    except Exception as e:
        return None, "%s will not import (%s)" % (mod_name, str(e)[:50])
    fn = getattr(mod, attr, None)
    if fn is None:
        return None, "%s has no %s()" % (mod_name, attr)
    try:
        return extract(fn()), ""
    except Exception as e:
        return None, "%s.%s() raised (%s)" % (mod_name, attr, str(e)[:50])


def organ_coverage():
    """What each organ actually names. -> {organ: (names|None, why_unknown)}"""
    out = {}
    # EAGLE — the watchdog's last look at the running system, published on the status poll.
    out["eagle"] = _ask("control_app", "eagle_state",
                        lambda r: _names_from((r or {}).get("rows") or (r or {}).get("checks")))
    # WATCHDOG — the health engine's own check rows.
    out["watchdog"] = _ask("health_engine", "report",
                           lambda r: _names_from((r or {}).get("rows") if isinstance(r, dict) else r))
    # DOCTOR — the console doctor's findings.
    out["doctor"] = _ask("console_doctor", "report",
                         lambda r: _names_from((r or {}).get("rows") if isinstance(r, dict) else r))
    # CORROBORATOR — the route sets compare siblings against each other and flag the odd one out.
    def _corr(_f):
        names = set()
        for m in ("chronicle_routes", "fleet_routes", "roster_routes"):
            try:
                mod = __import__(m)
                rep = mod.routes() if m == "chronicle_routes" else mod.routes(None)
                names |= _names_from(rep.get("routes"))
            except Exception:
                pass
        return names
    out["corroborator"] = (_corr(None), "") if _corr(None) else (None, "no route set answered")
    return out


def surfaces():
    """Everything that COULD be covered, derived from what already exists. -> {name: origin}"""
    found = {}
    try:
        import render_check as R
        for t in (R.TARGETS or {}):
            found[str(t)] = "render target"
    except Exception:
        pass
    try:
        import self_arming as SA
        for k in SA.LOCKS:
            found[k] = "valve"
        for k in getattr(SA, "ROUTES", {}):
            found[k] = "route"
    except Exception:
        pass
    try:
        import heart as H
        for v in (H.vessels().get("vessels") or []):
            n = v.get("name")
            if n:
                found.setdefault(str(n), "vessel")
    except Exception:
        pass
    return found


def _same_thing(surface, names):
    """Does the organ name this surface under a DIFFERENT string? -> bool

    Deliberately narrow: the tail after a dot, and singular/plural. Anything looser would start
    inventing coverage, which is the one thing this file must not do.
    """
    tail = surface.split(".")[-1].strip().lower()
    if not tail:
        return False
    cands = {tail, tail + "s", tail.rstrip("s")}
    for n in names:
        low = str(n).strip().lower()
        if low in cands or low.split(".")[-1] in cands:
            return True
    return False


def matrix():
    """-> (rows, organ_why). One row per surface, one cell per organ."""
    cov = organ_coverage()
    why = {o: cov[o][1] for o in ORGANS if cov.get(o) and cov[o][1]}
    rows = []
    for name, origin in sorted(surfaces().items()):
        cells = {}
        for o in ORGANS:
            names, _w = cov.get(o, (None, "not asked"))
            if names is None:
                cells[o] = UNKNOWN          # the ORGAN could not be asked — not the surface's fault
            elif name in names:
                cells[o] = COVERED
            else:
                # ⚠⚠ NOT COVERED AND NOT ABSENT — A THIRD THING, AND IT IS THE WHOLE ANSWER TO A3.
                # The corroborator names `runeword`, `sets`, `uniques`; the surface is
                # `chronicle.runeword`, `fleet.sets`. The organ IS watching this thing and calls
                # it something else, so a plain membership test reports ABSENT and the matrix
                # fills with holes that are not holes. That is the table he was shown.
                #
                # It is the same disjoint-vocabulary defect as A1's FLOWING (organ ids vs lane
                # names) and v2480's tab vocabulary (`unique` vs `uniques`) — three instances in
                # one day, which is a territory, not a coincidence.
                cells[o] = MISNAMED if _same_thing(name, names) else ABSENT
        rows.append({"surface": name, "origin": origin, "cells": cells,
                     "covered": sum(1 for v in cells.values() if v == COVERED),
                     "misnamed": sum(1 for v in cells.values() if v == MISNAMED),
                     "unknown": sum(1 for v in cells.values() if v == UNKNOWN)})
    return rows, why


def main(argv=None):
    rows, why = matrix()
    print("A3 — SURFACE × ORGAN, measured. COVERED = the organ names it · ABSENT = it runs and "
          "does not · UNKNOWN = the organ could not be asked at all\n")
    print("%-24s %-14s %s" % ("surface", "origin", "  ".join("%-12s" % o for o in ORGANS)))
    print("-" * 96)
    for r in rows:
        print("%-24s %-14s %s" % (r["surface"][:24], r["origin"],
                                  "  ".join("%-12s" % r["cells"][o] for o in ORGANS)))
    tot = len(rows)
    full = sum(1 for r in rows if r["covered"] == len(ORGANS))
    none = sum(1 for r in rows if r["covered"] == 0)
    mis = sum(r.get("misnamed", 0) for r in rows)
    print("\n%d surface(s): %d have all four organs, %d have none." % (tot, full, none))
    if mis:
        print("⚠ %d cell(s) are MISNAMED — the organ IS watching that thing and calls it "
              "something else. Those are not holes; they are a join nobody made, and reporting "
              "them as ABSENT is how this table came to look empty." % mis)
    if why:
        print("\n⚠ %d of %d organs could not be asked AT ALL, so their column is UNKNOWN "
              "everywhere — not empty:" % (len(why), len(ORGANS)))
        for o, w in sorted(why.items()):
            print("   %-14s %s" % (o, w))
        print("   An organ nobody can ask has not been shown to miss anything, and has not been "
              "shown to do anything either.")
    return 0


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
