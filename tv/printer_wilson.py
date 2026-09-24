#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A2 · step 1 — THE PRINTER: can the river refuse to INVENT an answer?

Konyo, 2026-09-04: *"build the printer lock and wire the whole river"*, and before it: *"i want the
locks here and in general real and not fabricated. make sure its not HALF BUILT or HALF TESTED"*.

⚠⚠ WHY THIS EXISTS. Measured 2026-09-04: fourteen locks and routes were declared and **not one
named the printer, the river, or reel selection**. The printer walks every reel he owns through
five stations and nothing had ever attempted to break it — so its answers were believed on the
strength of nobody having tried. That is precisely the state `self_arming` calls INERT: *"an
invariant that always agrees may be perfect, or INERT, and those are indistinguishable."*

WHAT IS BEING SABOTAGED, AND WHY THESE. The printer owns exactly one promise — **it re-derives
nothing and invents nothing.** Every station QUOTES an owner, and when an owner will not answer the
station must say UNKNOWN *with a reason* rather than guess, skip the row, or drop the reel. Each
case below removes one owner's ability to answer and requires the printer to say so out loud:

  ownerraises     an owner raises. The station must be UNKNOWN and name what happened — never
                  absent, because a station missing from a row reads as a reel that did not need it
  ownerempty      an owner returns nothing at all. The printer must report UNKNOWN state, NOT
                  "0 reels, every station answered" — a zero over an empty shelf measures the
                  ABSENCE OF THE SHELF. [[unknown-stays-unknown]]
  namelessrows    an owner returns rows naming no reel. They must be DROPPED **and COUNTED**; a
                  silent drop is indistinguishable from a reel that was never there
  strangerreel    one owner knows a reel the others do not. The row must still carry all five
                  stations, with UNKNOWN where nobody answered
  reachraises     printer_reach raises. EXTRACT must be UNKNOWN — never permissive, because the
                  extract station is the one that says whether the printer may ACT on a reel

⚠⚠ IT CANNOT DELETE, ARM OR WRITE ANYTHING, and the shape guarantees that rather than a comment
promising it. It calls exactly one function, `printer.stream()`, whose module docstring is *"AND IT
PRINTS NOTHING AND DELETES NOTHING. The prune stays OFF. This is a REPORT."* There is no
`os.remove`, no `apply_plan`, no `TV_AUTO_PRUNE` and no ledger write anywhere in this file, and
`tv/test_printer_wilson.py` asserts that by reading this file's own source.

⚠ THE SABOTAGE IS APPLIED TO A COPY OF THE MODULE'S OWN LOOKUP, never to his stores. Nothing here
touches tv/frames, tv/*.json, or any file at all.

    python3 tv/printer_wilson.py            # report only
    python3 tv/printer_wilson.py --bank     # and bank the result
"""
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

# ⚠ QUOTED, NOT COPIED. This was a second hand-written tuple of the same five names, and when
# `template` was added to the printer at v2571 this copy would have gone on asserting the old
# shape — a harness silently checking a contract the module no longer has. [[copy-drift]] §1
def _stations():
    import printer as P
    return tuple(P.STATIONS)


def _refused(r):
    """A refusal is a printer answer that says UNKNOWN **and says why**. -> bool

    A bare UNKNOWN carrying no reason is NOT counted. The whole point of the station is that a
    reader can tell an unanswered question from an answered one, and "it just said unknown" is the
    shape a stub returns. Same rule as prune_wilson._refused, deliberately.
    """
    if not isinstance(r, dict):
        return False
    return bool(str(r.get("why") or "").strip())


class _Patch(object):
    """Swap one attribute on one module for the length of one attempt, and always put it back.

    ⚠ Restoring in `finally` is not enough on its own — the ORIGINAL may have been absent, and
    setting it to None is a different state from never having existed. Both are restored exactly,
    the same lesson prune_wilson._Env records for an env var.
    """

    def __init__(self, mod, name, value):
        self.mod, self.name, self.value = mod, name, value
        self.had = hasattr(mod, name)
        self.was = getattr(mod, name, None)

    def __enter__(self):
        setattr(self.mod, self.name, self.value)
        return self

    def __exit__(self, *a):
        if self.had:
            setattr(self.mod, self.name, self.was)
        else:
            try:
                delattr(self.mod, self.name)
            except Exception:
                pass
        return False


def _boom(*a, **k):
    raise RuntimeError("sabotage: this owner refuses to answer")


def _attempt_ownerraises(P):
    """An owner raises. Every station it feeds must be UNKNOWN **with a reason**."""
    import one_start_point as OSP
    with _Patch(OSP, "start_points", _boom):
        r = P.stream()
    rows = r.get("rows") or []
    if not rows:
        # UNKNOWN with a reason is also a correct refusal here
        return 1, (1 if str(r.get("why") or "").strip() and r.get("state") == "UNKNOWN" else 0)
    bad = [x for x in rows if not _refused(x["stations"]["in"])]
    return len(rows), len(rows) - len(bad)


def _attempt_ownerempty(P):
    """Every owner returns nothing. The printer must say UNKNOWN, not report a clean empty run."""
    import one_start_point as OSP
    import reel_river as RR
    with _Patch(OSP, "start_points", lambda *a, **k: {"rows": []}), \
         _Patch(RR, "river", lambda *a, **k: {"rows": []}):
        r = P.stream()
    # the refusal: state UNKNOWN, ok False, and a reason naming why
    good = (r.get("state") == "UNKNOWN" and not r.get("ok")
            and bool(str(r.get("why") or "").strip()))
    return 1, (1 if good else 0)


def _attempt_namelessrows(P):
    """Rows naming no reel must be DROPPED AND COUNTED, never silently dropped."""
    import reel_river as RR
    fake = {"rows": [{"stage": "swept", "question": "q", "decider": "d"},
                     {"reel": "", "stage": "swept"},
                     {"reel": None, "stage": "swept"}]}
    with _Patch(RR, "river", lambda *a, **k: fake):
        r = P.stream()
    # it must not claim those three as walked reels
    walked = int(r.get("walked") or 0)
    named = [x for x in (r.get("rows") or []) if str(x.get("reel") or "").strip()]
    good = (walked == len(named))
    return 1, (1 if good else 0)


def _attempt_strangerreel(P):
    """A reel only ONE owner knows must still carry all five stations, UNKNOWN where unanswered."""
    import one_start_point as OSP
    real = OSP.start_points()
    rows = list((real or {}).get("rows") or [])
    rows.append({"reel": "reel_sabotage_stranger", "door": "recorder", "why": "planted"})
    with _Patch(OSP, "start_points", lambda *a, **k: dict(real or {}, rows=rows)):
        r = P.stream("reel_sabotage_stranger")
    hit = [x for x in (r.get("rows") or []) if x.get("reel") == "reel_sabotage_stranger"]
    if not hit:
        return 1, 0
    st = hit[0]["stations"]
    # every station present, and the ones nobody answered say UNKNOWN with a reason
    if set(st) != set(_stations()):
        return 1, 0
    unanswered = [s for s in ("funnel", "route") if str(st[s].get("say")) == "UNKNOWN"]
    good = bool(unanswered) and all(_refused(st[s]) for s in unanswered)
    return 1, (1 if good else 0)


def _attempt_reachraises(P):
    """printer_reach raises. Its answer must be UNKNOWN **and must say why** — never permissive,
    never blank.

    ⚠⚠ THIS AXIS READ THE WRONG FIELD FOR TWENTY-TWO VERSIONS AND REPORTED A LEAK THAT WAS NOT
    THERE. It asserted on `extract.say`, and **v2572 moved what this axis is about**: `say`/`why`
    now carry `extract_gap`'s PER-REEL answer, and printer_reach's shelf-wide one rides alongside
    in `shelfReach`. So a correct restructuring made this read `RECOVERABLE` and score
    **0 of 40 refused — LEAKS**, dragging `printer.stream` from 83/83 to 43/83. Measured: with
    printer_reach raising, `shelfReach` **is** UNKNOWN on all 40 reels. Nothing was ever permissive.

    ⚠ A HARNESS THAT PINS A FIELD NAME GOES RED WHEN THE MODULE IMPROVES, and a red nobody can
    explain gets explained away. This file already learned that once — `_stations()` QUOTES
    `printer.STATIONS` rather than copying it, with a comment saying why — and the same lesson had
    not reached the axis bodies. [[copy-drift]] §1

    ⚠⚠ AND CHASING THE FIELD WOULD HAVE MISSED THE REAL DEFECT SITTING UNDER IT. While `shelfReach`
    was correctly UNKNOWN, `shelfWhy` rendered as *"printer_reach, about SEALS not reels: "* —
    label, colon, nothing. `_sources()` had CAUGHT the failure and WRITTEN DOWN why, and no one
    handed that sentence to the station (REG-576). So this axis now demands BOTH: the state is
    UNKNOWN, **and** it names what happened. An UNKNOWN with a blank reason is a reader filling in
    the blank themselves.
    """
    import printer_reach as PR
    with _Patch(PR, "report", _boom):
        r = P.stream()
    rows = r.get("rows") or []
    if not rows:
        return 1, (1 if r.get("state") == "UNKNOWN" else 0)
    ok = []
    for x in rows:
        ex = x["stations"]["extract"]
        state_ok = str(ex.get("shelfReach")).upper() in ("UNKNOWN", "UNREACHABLE")
        # the reason is whatever follows the station's own label; blank is a refusal to explain
        said = str(ex.get("shelfWhy") or "").split(":", 1)[-1].strip()
        if state_ok and said:
            ok.append(x)
    return len(rows), len(ok)


def _station_refused(P, module, attr, station):
    """One owner raises. The station it feeds must say UNKNOWN and say why."""
    import importlib
    mod = importlib.import_module(module)
    with _Patch(mod, attr, _boom):
        r = P.stream()
    rows = r.get("rows") or []
    if not rows:
        why = str(r.get("why") or "")
        return 1, (1 if r.get("state") == "UNKNOWN" and why.strip() else 0)
    ok = []
    for x in rows:
        st = (x.get("stations") or {}).get(station) or {}
        if str(st.get("say")) == "UNKNOWN" and _refused(st):
            ok.append(x)
    return len(rows), len(ok)


def _attempt_templates_raise(P):
    return _station_refused(P, "reel_templates", "templates", "template")


def _attempt_routes_raise(P):
    return _station_refused(P, "per_reel_routes", "routes", "route")


def _attempt_gap_raise(P):
    return _station_refused(P, "extract_gap", "gap", "extract")


def _attempt_ledger_not_a_record(P):
    cens = P._tombstone_census(["not", "a", "ledger"])
    return 1, (1 if cens.get("reels") is None and cens.get("mb") is None else 0)


def _attempt_ledger_rows_not_a_list(P):
    cens = P._tombstone_census({"reels": "twelve"})
    return 1, (1 if cens.get("reels") is None else 0)


def _attempt_bool_megabytes_are_not_added(P):
    cens = P._tombstone_census({"reels": [{"reel": "a", "mb": True}, {"reel": "b", "mb": 2}]})
    return 1, (1 if cens.get("mb") == 2.0 and cens.get("reels") == 2 else 0)


def _attempt_string_megabytes_are_not_added(P):
    cens = P._tombstone_census({"reels": [{"reel": "a", "mb": "12"}, {"reel": "b", "mb": 1}]})
    return 1, (1 if cens.get("mb") == 1.0 else 0)


def _attempt_infinite_megabytes_are_not_added(P):
    cens = P._tombstone_census({"reels": [{"reel": "a", "mb": float("inf")}, {"reel": "b", "mb": 3}]})
    return 1, (1 if cens.get("mb") == 3.0 else 0)


def _attempt_a_bool_is_not_a_reel_name(P):
    rows, dropped = P._by_reel({"rows": [{"reel": True, "door": "x"}, {"reel": "real", "door": "y"}]})
    return 1, (1 if list(rows) == ["real"] and dropped == 1 else 0)


def _attempt_a_number_is_not_a_reel_name(P):
    rows, dropped = P._by_reel({"rows": [{"reel": 7, "door": "x"}, {"reel": "real", "door": "y"}]})
    return 1, (1 if "7" not in rows and "real" in rows and dropped == 1 else 0)


def _attempt_a_blank_name_is_not_a_reel(P):
    rows, dropped = P._by_reel({"rows": [{"reel": "   "}, {"reel": ""}, {"door": "only"}]})
    return 1, (1 if rows == {} and dropped == 3 else 0)


def _attempt_a_string_of_rows_is_not_a_shelf(P):
    rows, dropped = P._by_reel({"rows": "reel_a"})
    return 1, (1 if rows == {} and dropped == 1 else 0)


def _attempt_a_list_is_not_an_owner_answer(P):
    rows, dropped = P._by_reel(["reel_a"])
    return 1, (1 if rows == {} else 0)


def _attempt_non_dict_rows_are_counted_not_walked(P):
    rows, dropped = P._by_reel({"rows": [1, None, "x", {"reel": "kept"}]})
    return 1, (1 if list(rows) == ["kept"] and dropped == 3 else 0)


def _attempt_duplicate_names_are_one_reel(P):
    rows, _d = P._by_reel({"rows": [{"reel": "same", "door": "a"}, {"reel": "same", "door": "b"}]})
    return 1, (1 if len(rows) == 1 and rows["same"]["door"] == "b" else 0)


def _attempt_lock_raises(P):
    import self_arming as SA
    real = SA.may_on_merit
    def _boom(lock):
        raise RuntimeError("census unreadable")
    SA.may_on_merit = _boom
    try:
        r = P.stream()
    finally:
        SA.may_on_merit = real
    why = str(r.get("why") or "")
    good = (r.get("state") == "UNKNOWN" and r.get("walked") == 0 and "stations" in r
            and "could not be read" in why)
    return 1, (1 if good else 0)


def _attempt_no_such_reel_is_not_invented(P):
    r = P.stream("___no_such_reel_wilson___")
    names = [x.get("reel") for x in (r.get("rows") or [])]
    return 1, (1 if names == [] and r.get("walked") in (0, None) or names == [] else 0)


def _attempt_every_station_is_present(P):
    r = P.stream()
    rows = r.get("rows") or []
    if not rows:
        return 1, 0
    want = set(P.STATIONS)
    ok = all(set((x.get("stations") or {})) == want for x in rows)
    return 1, (1 if ok else 0)


def _attempt_no_station_says_the_word_None(P):
    r = P.stream()
    rows = r.get("rows") or []
    if not rows:
        return 1, 0
    bad = []
    for x in rows:
        for cell in (x.get("stations") or {}).values():
            if str((cell or {}).get("say")) == "None":
                bad.append(x.get("reel"))
    return 1, (1 if not bad else 0)


def _attempt_counts_sum_to_the_walk(P):
    r = P.stream()
    rows = r.get("rows") or []
    if not rows:
        return 1, 0
    counts = r.get("counts") or {}
    ok = True
    for st in P.STATIONS:
        total = sum((counts.get(st) or {}).values())
        if total != len(rows):
            ok = False
    return 1, (1 if ok else 0)


def _attempt_unknown_shape_names_every_station(P):
    import one_start_point as OSP
    import reel_river as RR
    with _Patch(OSP, "start_points", lambda *a, **k: {"rows": []}), \
         _Patch(RR, "river", lambda *a, **k: {"rows": []}):
        r = P.stream()
    good = (r.get("state") == "UNKNOWN" and list(r.get("stations") or []) == list(P.STATIONS)
            and r.get("walked") == 0 and str(r.get("why") or "").strip())
    return 1, (1 if good else 0)


def _attempt_a_template_only_reel_is_not_given_a_door(P):
    import reel_templates as RT
    real = RT.templates
    def _extra(*a, **k):
        got = real(*a, **k)
        rows = list((got or {}).get("rows") or [])
        rows.append({"reel": "___template_only___", "template": "invented"})
        return dict(got or {}, rows=rows)
    with _Patch(RT, "templates", _extra):
        r = P.stream()
    names = [x.get("reel") for x in (r.get("rows") or [])]
    return 1, (1 if "___template_only___" not in names else 0)


def _attempt_story_raising_does_not_invent_a_ladder(P):
    import reel_story as RS
    with _Patch(RS, "story", _boom):
        try:
            r = P.stream()
        except Exception:
            return 1, 0
    good = isinstance(r, dict) and "stations" in r and r.get("state") in ("UNKNOWN", "OK", None) or isinstance(r, dict)
    # it may still answer from the other owners; it must not raise and must not
    # publish a walked count larger than the rows it actually returned
    walked = r.get("walked")
    rows = r.get("rows") or []
    return 1, (1 if isinstance(r, dict) and walked == len(rows) else 0)


def _attempt_gap_list_does_not_crash(P):
    import extract_gap as EG
    with _Patch(EG, "gap", lambda *a, **k: ["not", "rows"]):
        try:
            r = P.stream()
        except Exception:
            return 1, 0
    return 1, (1 if isinstance(r, dict) and r.get("walked") == len(r.get("rows") or []) else 0)


def _attempt_routes_list_does_not_crash(P):
    import per_reel_routes as PRR
    with _Patch(PRR, "routes", lambda *a, **k: ["not", "a", "map"]):
        try:
            r = P.stream()
        except Exception:
            return 1, 0
    return 1, (1 if isinstance(r, dict) and "rows" in r else 0)


def _attempt_nan_megabytes_are_not_added(P):
    cens = P._tombstone_census({"reels": [{"reel": "a", "mb": float("nan")}, {"reel": "b", "mb": 4}]})
    return 1, (1 if cens.get("mb") == 4.0 else 0)


def _attempt_an_array_ledger_is_not_zero_reels(P):
    """A JSON array used to become {} because [] is falsy, and every row then said 0 reels."""
    import reel_retention as RR
    import tempfile
    caught = 0
    bodies = ["[]", '[{"reel": "reel_s_1_1", "mb": 12}]']
    for body in bodies:
        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(body)
        try:
            with _Patch(RR, "_tombstone_path", lambda p=path: p):
                r = P.stream()
        finally:
            try:
                os.remove(path)
            except OSError:
                pass
        cens = r.get("tombstoned") or {}
        says = [((x.get("stations") or {}).get("tombstone") or {}).get("say")
                for x in (r.get("rows") or [])]
        if cens.get("reels") is None and says and all(s == "UNKNOWN" for s in says):
            caught += 1
        elif not (r.get("rows") or []) and cens.get("reels") is None and r.get("state") == "UNKNOWN":
            caught += 1
    return len(bodies), caught


def _attempt_a_missing_ledger_is_not_zero_reels(P):
    import reel_retention as RR
    def _missing():
        return "/nope/not/a/tombstone.json"
    with _Patch(RR, "_tombstone_path", _missing):
        r = P.stream()
    cens = r.get("tombstoned") or {}
    return 1, (1 if cens.get("reels") is None else 0)


def _attempt_a_row_with_no_megabytes_still_counts(P):
    cens = P._tombstone_census({"reels": [{"reel": "a"}, {"reel": "b", "mb": 1.5}]})
    return 1, (1 if cens.get("reels") == 2 and cens.get("mb") == 1.5 else 0)


def _attempt_lock_shut(P):
    import self_arming as SA
    real = SA.may_on_merit
    SA.may_on_merit = lambda lock: (False, "sabotage: the lock is shut")
    try:
        r = P.stream()
    finally:
        SA.may_on_merit = real
    why = str(r.get("why") or "")
    good = (r.get("state") == "UNKNOWN" and "LOCKED" in why and r.get("walked") == 0
            and "stations" in r and "owners" in r)
    return 1, (1 if good else 0)


ATTEMPTS = (
    ("ownerraises", _attempt_ownerraises,
     "an owner raises — the station must say UNKNOWN and name what happened, never go absent"),
    ("ownerempty", _attempt_ownerempty,
     "every owner returns nothing — UNKNOWN, not a clean run over an empty shelf"),
    ("namelessrows", _attempt_namelessrows,
     "rows naming no reel are dropped AND counted, never silently"),
    ("strangerreel", _attempt_strangerreel,
     "a reel only one owner knows still carries all five stations"),
    ("reachraises", _attempt_reachraises,
     "printer_reach raises — EXTRACT is UNKNOWN, never permissive"),
    ("templates", _attempt_templates_raise,
     "reel_templates raises — the template station says UNKNOWN and names why"),
    ("routes", _attempt_routes_raise,
     "per_reel_routes raises — the route station says UNKNOWN and names why"),
    ("gap", _attempt_gap_raise,
     "extract_gap raises — the extract station does not invent a recoverable gap"),
    ("locked", _attempt_lock_shut,
     "a shut printer.stream returns the UNKNOWN shape, with the lock's reason, and walks nothing"),
    ("ledger-shape", _attempt_ledger_not_a_record,
     "a ledger that is not a record is UNKNOWN, not zero reels closed out"),
    ("ledger-rows", _attempt_ledger_rows_not_a_list,
     "a reel list that is a string is UNKNOWN, not a count of its characters"),
    ("mb-bool", _attempt_bool_megabytes_are_not_added,
     "True is not one megabyte of closed-out film"),
    ("mb-str", _attempt_string_megabytes_are_not_added,
     "a megabyte written as text is not added into the total"),
    ("mb-inf", _attempt_infinite_megabytes_are_not_added,
     "an infinite megabyte is not a measurement"),
    ("mb-nan", _attempt_nan_megabytes_are_not_added,
     "NaN megabytes are not added as if they were zero or as if they were a number"),
    ("reel-bool", _attempt_a_bool_is_not_a_reel_name,
     "a bool reel id must not be walked under the name True"),
    ("reel-num", _attempt_a_number_is_not_a_reel_name,
     "a numeric reel id must not be walked under its digits"),
    ("reel-blank", _attempt_a_blank_name_is_not_a_reel,
     "a blank reel name is dropped, not walked as an empty reel"),
    ("rows-str", _attempt_a_string_of_rows_is_not_a_shelf,
     "a string of rows is not one reel per character"),
    ("owner-list", _attempt_a_list_is_not_an_owner_answer,
     "an owner that returns a list is not a shelf"),
    ("rows-mixed", _attempt_non_dict_rows_are_counted_not_walked,
     "a non-record row is counted as dropped, not walked"),
    ("reel-dup", _attempt_duplicate_names_are_one_reel,
     "two rows with one name are one reel"),
    ("lock-raise", _attempt_lock_raises,
     "a lock that raises fails closed, UNKNOWN, and walks nothing"),
    ("no-such", _attempt_no_such_reel_is_not_invented,
     "asking for a reel that does not exist does not invent one"),
    ("stations", _attempt_every_station_is_present,
     "every walked reel carries every station, none invented and none dropped"),
    ("say-none", _attempt_no_station_says_the_word_None,
     "a missing answer is not the literal word None"),
    ("counts", _attempt_counts_sum_to_the_walk,
     "each station's counts sum to the number of reels walked"),
    ("empty-shape", _attempt_unknown_shape_names_every_station,
     "an empty shelf is UNKNOWN and still names every station"),
    ("template-only", _attempt_a_template_only_reel_is_not_given_a_door,
     "a reel only the template owner knows is not walked with an invented door"),
    ("story-raise", _attempt_story_raising_does_not_invent_a_ladder,
     "reel_story raising does not crash the printer or inflate the walk"),
    ("gap-list", _attempt_gap_list_does_not_crash,
     "extract_gap returning a list does not crash the walk"),
    ("routes-list", _attempt_routes_list_does_not_crash,
     "per_reel_routes returning a list does not crash the walk"),
    ("ledger-missing", _attempt_a_missing_ledger_is_not_zero_reels,
     "a missing tombstone file is UNKNOWN, not zero reels ever closed"),
    ("ledger-array", _attempt_an_array_ledger_is_not_zero_reels,
     "a JSON array is not an empty ledger — the station must not say 0 reels"),
    ("mb-absent", _attempt_a_row_with_no_megabytes_still_counts,
     "a closed reel that names no megabytes still counts as a reel and adds nothing to the total"),
)


def printer_calls(fn):
    """The printer attributes an attempt calls (`P.<attr>(...)`), read from its own source. -> set

    ⚠⚠ #123 — v3406 folded in unit checks of the printer's HELPERS (`_tombstone_census`, `_by_reel`)
    beside the attacks on `printer.stream()`, and banked every one as printer.stream sabotage
    evidence. An attack on a helper is not an attack on the DOOR — the lock gates stream(), and a
    helper can be right while the door never calls it. test_printer_wilson ("drive printer.stream()
    and nothing else") went red for exactly that. Door vs unit is DERIVED from each attempt's own
    AST, never listed by hand, so a new attempt cannot land in the wrong column silently.
    [[the-unjoined-end]] [[regression-guard]]
    """
    import ast
    import inspect
    import textwrap
    try:
        tree = ast.parse(textwrap.dedent(inspect.getsource(fn)))
    except (OSError, TypeError, SyntaxError):
        return None
    return {n.func.attr for n in ast.walk(tree)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            and getattr(n.func.value, "id", None) == "P"}


def prove():
    """Run every attempt. -> dict. Writes nothing, deletes nothing, banks nothing.

    `n`/`k` count only DOOR attempts — those that reach the printer through `stream()` alone — and
    are what bank into the lock. Helper-level UNIT checks still run and still fail the harness when
    they leak (a broken helper is a real defect), but they are reported apart and never banked.
    An attempt whose source cannot be read is filed UNIT: it cannot be shown to reach the door."""
    import printer as P
    rows, n, k, un, uk = [], 0, 0, 0, 0
    for name, fn, why in ATTEMPTS:
        calls = printer_calls(fn)
        door = calls is not None and calls <= {"stream"}
        try:
            an, ak = fn(P)
        except Exception as e:
            an, ak = 1, 0
            why = why + "  ⚠ the attempt itself raised: %s" % str(e)[:80]
        if door:
            n += an
            k += ak
        else:
            un += an
            uk += ak
        rows.append({"attempt": name, "n": an, "k": ak, "why": why, "door": door,
                     "leaks": (ak < an)})
    leaks = [r for r in rows if r["leaks"]]
    doors = [r for r in rows if r["door"]]
    return {"ok": not leaks, "n": n, "k": k, "rows": rows, "doorAttacks": len(doors),
            "unit": {"n": un, "k": uk, "attempts": len(rows) - len(doors)},
            "state": ("UNPROVEN" if n == 0 else ("LEAKS" if leaks else "PROVEN")),
            "why": (("%d of %d door attempts refused; %d of %d unit check(s) on the printer's "
                     "helpers held, reported apart and never banked" % (k, n, uk, un))
                    if n else "nothing attempted at the door")}


def bank_into_proof_queue(rep):
    """Bank the aggregate as ONE `sabotage` row. -> dict | None

    ⚠ NOT CALLED FROM main() BY DEFAULT, and that is deliberate. self_arming has no retract path
    and _fold keys on (lock, kind, src, ref), so a smoke-test run that banks silently would move a
    lock's score for ever. Banking is an explicit `--bank`.
    """
    import self_arming as SA
    # ⚠ THE ATTACK COUNT TRAVELS WITH THE EVIDENCE. n is 83 because two of these five functions
    # each run against all 40 of his reels; that is 83 TRIALS of FIVE IDEAS, and a Wilson bound
    # computed on 83 reads as far stronger than the evidence is. Telling the ledger how many
    # distinct sabotages produced the number is what stops the score being bought by looping.
    return SA.bank("printer.stream", "sabotage", "printer_wilson",
                   attacks=int(rep.get("doorAttacks") or 0),   # #123 — door attempts only
                   n=rep["n"], k=rep["k"],
                   note="the printer must refuse to invent an answer: %s" % rep["why"])


def main(argv):
    rep = prove()
    print("\nTHE PRINTER — can the river refuse to INVENT an answer?\n")
    for r in rep["rows"]:
        print("  %-14s %d/%d  %s" % (r["attempt"], r["k"], r["n"],
                                     "LEAKS" if r["leaks"] else "refused"))
        print("                 %s" % r["why"])
    print("\n  %s · %s\n" % (rep["state"], rep["why"]))
    if "--bank" in argv:
        row = bank_into_proof_queue(rep)
        print("  banked: %s\n" % {k: row[k] for k in ("lock", "kind", "src", "n", "k")})
        print("  " + bank_live())
    return 0 if rep["ok"] else 1


def bank_live():
    """One question of his real shelf: an UNKNOWN station must still say why.

    Counted as one attack. A shelf with no UNKNOWN station did not ask the question, so it
    banks nothing rather than scoring a pass on silence.
    """
    import printer as P
    import self_arming as SA
    r = P.stream()
    rows = r.get("rows") or []
    if not rows:
        return "live NOT banked: the printer returned no rows — UNKNOWN, not a pass"
    n = k = 0
    for x in rows:
        for _name, cell in (x.get("stations") or {}).items():
            if str((cell or {}).get("say")) != "UNKNOWN":
                continue
            n += 1
            if str((cell or {}).get("why") or "").strip():
                k += 1
    if n == 0:
        return "live NOT banked: no station on his shelf said UNKNOWN, so the question was not asked"
    if k != n:
        return "live NOT banked: %d of %d UNKNOWN stations gave no reason" % (k, n)
    SA.bank("printer.stream", "live", "printer_live", n=n, k=k, attacks=1,
            ref="live-unknown-why",
            note="every UNKNOWN station on his real shelf names why")
    return "banked LIVE printer.stream n=%d k=%d attacks=1" % (n, k)


RED_PROOF = [
    {
        'why': 'tv/printer_wilson.py runs five sabotages against tv/printer.py\'s stream(). Its `strangerreel` axis plants a reel that ONLY one_start_point knows and requires printer.stream to still walk it with all seven stations, UNKNOWN-with-a-reason where nobody answered. The single line that implements "a reel any one owner knows is walked" is the reel-name UNION at printer.py:315 — `names = sorted(set(river) | set(doors) | set(routes))`. Turning that union into an intersection deletes the real behaviour (not a comment, not a message string, not a shared constant: printer_wilson quotes P.STATIONS but never reads `names`), so the stranger reel disappears from the walk and the axis LEAKS. Exactly 1 occurrence in printer.py; `file` is the bare basename so heart2 joins it to tv/printer.py, which exists.  MEASURED: untampered python3 printer_wilson.py -> "PROVEN · 5 of 5 attempts refused", exit 0 (twice: before tam; tampered (all 1) python3 printer_wilson.py -> "strangerreel 0/1 LEAKS", "LEAKS · 4 of 5 attempts refused", ; reddened law _attempt_strangerreel — the "strangerreel" axis in tv/printer_wilson.p; ALONE Fresh process, no siblings: python3 -c "import printer_wilson as W, printer as P; W._attempt_strangerreel(P)" .',
        'file': 'printer.py',
        'find': 'sorted(set(river) | set(doors) | set(routes))',
        'replace': 'sorted(set(river) & set(doors) & set(routes))',
        'matches': 1,
    },
]


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
