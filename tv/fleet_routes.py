"""A21c — THE FLEET LANES, on the same heart, judged by the same corroborator.

Konyo, 2026-09-03, after the set denominator came back null on every read:
*"sync them and connect it to the heart of the console the fleet"*

WHAT A FLEET LANE IS. Each figure on a fleet card — sets, uniques, runewords — travels the same
chain, and a break anywhere makes the number unreadable rather than wrong:

    board getter  ->  probe asks it  ->  total on the wire  ->  a unit on screen

⚠ THIS EXISTS BECAUSE ALL FOUR LOOKED FINE AND ONE WAS MISSING. `window._gSetRoster` was never
defined in bible.html. The probe asked for it anyway, `undefined` came back, `setsTotal` was null
on every read since the feature shipped, and the card printed a bare "121" with an indeterminate
bar. v2163 had fixed precisely this for uniques and runewords after a cross-family review and left
the third twin running. Nothing compared the three lanes to each other, so the one that could not
answer looked exactly like the two that could.

THE CORROBORATOR IS THE SAME FUNCTION the chronicle routes use — `chronicle_routes.corroborate`.
Not a copy of its rule: the same code. Two spellings of one rule only ever get fixed once, and
this whole module is what that costs. [[copy-drift]] [[the-unjoined-end]]
"""
import io
import os
# ⚠ THE ONE PRODUCER. Every route set quotes this rather than its own reading, so three surfaces
# cannot drift apart again. Imported defensively: if it will not load, `total()` is simply absent
# and the row goes UNKNOWN — which is the honest state, and better than a lane inventing a total.
try:
    import route_totals as _rt
except Exception:          # pragma: no cover - a tree without the producer still serves
    _rt = None


class _NoProducer(object):
    """Stands in when route_totals will not import. Everything is UNKNOWN, nothing is invented."""

    @staticmethod
    def total(_k):
        return None

    @staticmethod
    def disagreements(_rows, own_field=None):
        return []


if _rt is None:
    _rt = _NoProducer()

# ⚠ `_crt`, not `_cr`: both of these files already bind `_cr` with a
# function-local import further down, and a name assigned anywhere in a function
# is local for the WHOLE function — so using `_cr` above it raised
# UnboundLocalError and the route state kept reporting ok:False with a new
# reason. A fix that fails like the bug it replaces is the worst kind.
import chronicle_routes as _crt
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BIBLE = os.path.join(ROOT, "bible.html")

# lane -> (the board getter it needs, the key the wire must carry)
LANES = (
    ("sets", "_gSetRoster", "setsTotal"),
    ("uniques", "_gUniqueRoster", "uniquesTotal"),
    ("runewords", "_rwTotalN", "runewordsTotal"),
)
LINKS = ("getter", "probe", "total", "unit")


def _defines(src, name):
    """Is `name` DEFINED on window, or merely mentioned? -> bool

    ⚠ `_gSetRoster` was named in `control_app.py` and in prose for months while no definition
    existed. A mention is the thing this must not count. [[source-reading-guard]]
    """
    return re.search(r"window\.%s\s*=" % re.escape(name), src) is not None


# ⚠ MEASURED BEFORE IT SHIPPED: deriving this cost 6.1 s, and `heart_state()` — which runs on a
# CLICK — went to 16.4 s cold. The scan AST-parses every file in this directory, one of which is a
# 25,000-line test suite, and it did that on every single open. A derivation this expensive behind
# a button is the poll-slower-than-its-interval shape wearing a different hat.
#
# The cache is keyed on what it READ, not on a clock: the newest mtime and the file count across
# the sources. Touch any of them and it re-derives on the next call. A time-based TTL would have
# been simpler and would have answered from a stale tree for its whole window, which is the exact
# thing this module exists to catch other people doing. [[stale-reading]]
_MEMO = {"key": None, "val": None}


def _source_key():
    try:
        stamps = []
        for p in sorted(os.listdir(HERE)):
            if p.endswith(".py"):
                stamps.append(os.path.getmtime(os.path.join(HERE, p)))
        for extra in (BIBLE, os.path.join(HERE, "control_ui.html")):
            if os.path.isfile(extra):
                stamps.append(os.path.getmtime(extra))
        for p in sorted(os.listdir(HERE)):
            if p.endswith("_roster.json"):
                stamps.append(os.path.getmtime(os.path.join(HERE, p)))
        # ⚠ BIBLE GETS ITS OWN SLOT — see the note in chronicle_routes._source_key. `max` is a
        # lossy digest and cannot tell a bible.html change from no change whenever another source
        # carries a newer mtime, and bible.html is where the counts come from since v2484.
        # ⚠⚠ A FAILED STAT MAY NOT BECOME A READING. This said `_bib = 0` on any failure, and
        # 0 is indistinguishable from a real mtime — so an unreadable bible.html would produce a
        # STABLE key, which is precisely the staleness this slot was added to prevent: the rows
        # would cache forever against a file nobody could read. His swallow ratchet caught it
        # within the hour (baseline 74 -> 77, three new sites, one per route module) and it was
        # right. Unkeyable means NOT CACHED, which is slow and never wrong — the same answer the
        # outer handler already gives. [[unknown-stays-unknown]]
        try:
            if not os.path.isfile(BIBLE):
                return None
            _bib = round(os.path.getmtime(BIBLE), 3)
        except Exception:
            return None
        return (len(stamps), round(max(stamps), 3) if stamps else 0, _bib)
    except Exception:
        return None                     # unkeyable -> never cached, which is slow and never wrong


#: Envelope fields that are NOT lanes. `at` is excluded from the memo key on purpose (see below).
_TALLY_ENVELOPE_SKIP = ("at",)


def _tally_key(tally):
    """Kept as a name because this module's tests and callers use it; the BODY moved.

    ⚠ It delegates rather than duplicating. roster_routes carried this same line unfixed for a
    version because v2473 fixed the file in front of it and did not sweep the shape — the review
    found it dead on his console. Two copies of one rule is how that happens, so there is now one
    implementation in chronicle_routes and two quotations of it. [[copy-drift]] [[sweep-dont-ask]]
    """
    return _crt.tally_memo_key(tally)


def routes(tally=None):
    """-> dict, in the heart's four words. `tally` is the live per-lane payload when one is
    available; without it the `total` link is UNKNOWN, never absent."""
    # ⚠ THE KEY MUST INCLUDE THE ARGUMENT. The first cut keyed only on source mtimes, and this
    # function's answer also depends on the live tally handed to it — so a call made with no tally
    # cached UNKNOWN and the next call WITH a real tally got that UNKNOWN back. A cache whose key
    # omits an input is not a cache, it is a wrong answer with good latency. Its own guard caught
    # it within a minute of being written. [[stale-reading]]
    # ⚠⚠ AND THE VALUES ARE NOT ALL DICTS — that is what broke it. `tally` is an ENVELOPE, not a
    # map of lanes: measured on his live console it carries 8 keys of which only 3 are lanes
    # (runewords/sets/uniques -> {have,total}); the rest are `ok` (bool), `why` (None), `at` (int)
    # and `source`/`profile` (str). `(v or {}).get("total")` threw on the first scalar it met, so
    # `routes()` raised for every real call and the heart printed the fleet lanes as UNKNOWN with
    # "'bool' object has no attribute 'get'" — for days, on his screen. He was the detector.
    #
    # `at` is deliberately EXCLUDED: it is a fresh timestamp on every read, so folding it in would
    # change the key every call and the memo would never hit once. `profile` is deliberately
    # INCLUDED: main and ladder are different answers, and serving one for the other is the exact
    # shape of [[d2r-ladder-doctrine]]. [[stale-reading]] [[the-unjoined-end]]
    _k = _source_key()
    if _k is not None:
        _k = (_k, _tally_key(tally))
    if _k is not None and _MEMO["key"] == _k and _MEMO["val"] is not None:
        return _MEMO["val"]

    try:
        bible = io.open(BIBLE, encoding="utf-8", errors="replace").read()
    except Exception as e:
        return {"ok": False, "routes": [], "counts": None, "flags": [],
                "why": "bible.html could not be read (%s), so the lanes are UNKNOWN" % str(e)[:70]}
    try:
        probe = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8",
                        errors="replace").read()
    except Exception as e:
        return {"ok": False, "routes": [], "counts": None, "flags": [],
                "why": "the probe source could not be read (%s)" % str(e)[:70]}
    try:
        ui = io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8",
                     errors="replace").read()
    except Exception:
        # ⚠ NOT "". An unreadable control_ui.html made every `unit` search miss, so the lane
        # reported "the screen does not say what it is counting" — a fault blamed on the UI when
        # the truth is we could not open the file. None keeps the two apart and the link renders
        # UNKNOWN, which the badge already draws as "?". [[unknown-stays-unknown]]
        ui = None

    out = []
    for key, getter, wirekey in LANES:
        has_getter = _defines(bible, getter)
        asked = ("window.%s" % getter) in probe
        # the wire: only a LIVE tally can answer this. No tally -> UNKNOWN, never False.
        tot = None
        # ⚠ A TALLY THAT REFUSED IS NOT A TALLY THAT SAID ZERO. `grail_tally()` hands back
        # {'ok': False, 'why': '... these counts are UNKNOWN, not zero', 'sets': None, ...} when
        # the board cannot be read at all. Asking only `is not None` made every lane tot=False and
        # sent all three down the `not tot` branch, reading DARK with "the wire still carried no
        # total — the break is between them". That accuses the WIRE of a failure the BOARD already
        # explained, on machines where it is the normal state. Leaving tot as None keeps the lane
        # UNKNOWN, which is what it is. [[unknown-stays-unknown]]
        _refused = isinstance(tally, dict) and tally.get("ok") is False
        if tally is not None and not _refused:
            p = (tally or {}).get(key)
            tot = bool(isinstance(p, dict) and isinstance(p.get("total"), int) and p["total"] > 0)
        # the unit: does the surface say what the denominator is OVER
        unit = None if ui is None else bool(re.search(r"%s\s*:\s*\{w:" % re.escape(key), ui))

        lanes = {"getter": {"ok": has_getter, "by": [getter]},
                 "probe": {"ok": asked, "by": ["control_app.py"]},
                 "total": {"ok": tot, "by": [wirekey]},
                 "unit": {"ok": unit, "by": ["control_ui.html"]}}

        if not has_getter:
            state = "DARK"
            why = ("the board defines no %s, so the probe asks for a function that does not exist "
                   "and the total is null on every read — a number with no denominator, forever"
                   % getter)
        elif not asked:
            state = "DARK"
            why = ("the board can answer and nothing asks it — the value exists and never reaches "
                   "a screen")
        elif tot is None:
            state = "UNKNOWN"
            why = ("the board defines it and the probe asks for it; whether a total actually "
                   "arrives can only be told from a live read, and none was taken")
        elif not tot:
            state = "DARK"
            why = ("the getter exists and the probe asks, and the wire still carried no total — "
                   "the break is between them, which is the half a source read cannot see")
        elif not unit:
            state = "WATCHED"
            why = ("it reports a denominator and the surface never says what that denominator is "
                   "OVER — a right number under an unstated unit")
        else:
            state = "FLOWING"
            why = "defined, asked, reported, and the screen says what it is counting"
        # ⚠⚠ THE COUNT COMES FROM THE ONE PRODUCER, NOT FROM THIS LANE'S OWN READING. Until v2484
        # the three route sets each read a different source and the heart showed runeword 105 / 99
        # / 99 and unique 398 / 403 / 403 — every number right, and the panel reading as a
        # contradiction. His ruling: "sync and match them obivously.. no reason to have this gap".
        # This lane's own number is kept beside it, never dropped, and route_totals.disagreements()
        # says so out loud if the two ever differ. [[copy-drift]] [[unknown-stays-unknown]]
        out.append({"key": key, "state": state, "why": why, "lanes": lanes,
                    "count": _rt.total(key),
                    # the UNIT travels with the number, from the same producer. Sets count PIECES
                    # and the other two count entries; a section-wide noun could not say that, and
                    # a wrong unit is how "135 names" once meant 135 set pieces.
                    "noun": _rt.noun(key),
                    "boardCount": ((tally or {}).get(key) or {}).get("total") if tally else None})

    try:
        import chronicle_routes as _cr
        flags = _cr.corroborate(out)                 # THE SAME FUNCTION, not a second copy
    except Exception as e:
        flags = []
        return {"ok": True, "routes": out, "counts": _counts(out), "flags": flags,
                "why": "the corroborator could not be reached (%s), so no divergence was "
                       "looked for — that is UNKNOWN, not 'nothing diverges'" % str(e)[:70]}
    _out = {"ok": True, "why": "", "routes": out, "counts": _counts(out), "flags": flags,
            "lanes": list(LINKS)}
    if _k is not None:
        _MEMO["key"], _MEMO["val"] = _k, _out
    return _out


def _counts(rows):
    c = {"FLOWING": 0, "WATCHED": 0, "DARK": 0, "UNKNOWN": 0}
    for r in rows:
        c[r["state"]] = c.get(r["state"], 0) + 1
    return c


if __name__ == "__main__":
    import json
    import sys
    t = None
    if len(sys.argv) > 1 and sys.argv[1] == "--live":
        sys.path.insert(0, HERE)
        import control_app as ca
        t = ca._tally_cached()
    d = routes(t)
    print("FLEET LANES — %s" % (d.get("why") or "derived"))
    for r in d["routes"]:
        print("\n  %-10s %-8s n=%s" % (r["key"], r["state"], r["count"]))
        for ln in LINKS:
            v = r["lanes"][ln]
            mark = "OK " if v["ok"] else ("?? " if v["ok"] is None else "-- ")
            print("      %s%-9s %s" % (mark, ln, ", ".join(v["by"])))
        print("      -> %s" % r["why"])
    print("\n  counts: %s" % d["counts"])
    for f in d["flags"]:
        print("  ⚑ %s" % f["say"])
