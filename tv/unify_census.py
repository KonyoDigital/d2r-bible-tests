# -*- coding: utf-8 -*-
"""#44 — THE PREREQUISITE FOR REMOVING MINI: name every technique, and say whether ON AIR has it.

Konyo, 2026-09-08: *"soon they also will be and should be coming from a unified ON AIR ONLY STREAM
we will remove MINI out completely and leave ON AIR only but first make sure to harness every single
technique and every single template and every single thing related so no gaps are missing when you
finally leave and unify the ON AIR and MINI."*

⚠⚠ THE ORDER IS THE INSTRUCTION. The harness comes FIRST. Removing MINI before every technique it
carries is reproduced under ON AIR would silently drop read-paths, and the loss would surface as
reels that stop yielding names with nothing saying why — the shape this repo keeps paying for.

=== WHY THIS IS A MODULE AND NOT A MARKDOWN TABLE ===
A document is a claim about the code on the day it was written. Three of this repo's worst defects
were exactly that: a comment that outlived its referent, a count that stopped being true, a station
declared in prose that no code path could reach. This DERIVES the census on every run — the
templates from `reel_templates.ROUTES`, the scenarios from `extract_gap`'s own constants, and the
read-path gap from an AST call-graph over the shipped `control_app.py`. If a technique is added and
nobody teaches ON AIR about it, this turns it up without anyone remembering to look.

=== ⚠⚠ UNKNOWN IS A FIRST-CLASS VERDICT AND THE GATE COUNTS IT AS A BLOCKER ===
`reproduced=None` means NOBODY LOOKED, and it is not `False` (a measured gap, actionable) and
emphatically not `True`. `may_unify()` refuses while any technique is UNKNOWN, for the same reason
it refuses on a real gap: an unasked question and an answered one are opposite states.
[[unknown-stays-unknown]] [[zero-needs-a-denominator]]

⚠ MINI AUTO — the hover technique — is DELIBERATELY OUT OF SCOPE. His words: *"for the MINI
AUTOMATIC thats a different task in its own as it already is... we will leave it"*. It is #17/#41
and it is his. Folding it in here would put a decision he reserved inside a gate he did not ask for.
"""
import ast
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

#: The two streams, by the entry points a reader can actually name. ⚠ These are SEEDS for a
#: reachability walk, not the whole story — anything they call transitively is in scope.
MINI_ENTRIES = ("mini_start", "mini_state", "_mini_cells_from_live_frame", "_mini_seal",
                "_mini_watchdog")
ONAIR_ENTRIES = ("start_agent", "stop_agent", "_start_capture", "_stop_capture", "_capture_health")

#: Names that appear only on the MINI side but are NOT techniques — lifecycle plumbing that ON AIR
#: has its own equivalent of. Each carries the reason it is exempt, because an unexplained
#: exemption list is how a real gap gets waved through.
NOT_A_TECHNIQUE = {
    "_force_kill_all_agents": "shutdown plumbing — ON AIR calls it from its own stop path",
    "_console_beacon_async": "the console's liveness beacon, not a read-path",
    "_lane_tick": "the shared lane driver; both streams reach it through different callers",
    "_lane_waking": "lane-state bookkeeping shared by every lane",
}


def _fn_calls(path):
    """name -> set of names it calls, over one module. -> (dict, why)

    ⚠ AN AST WALK, NOT A GREP. Three guards in this repo have been satisfied by their own comments.
    Text search cannot tell a call from a sentence describing one. [[source-reading-guard]]
    """
    try:
        src = io.open(path, encoding="utf-8").read()
    except Exception as exc:
        return None, "%s could not be read (%s)" % (os.path.basename(path), type(exc).__name__)
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        return None, "%s does not parse (%s)" % (os.path.basename(path), exc.msg)
    out = {}
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            calls = set()
            for c in ast.walk(n):
                if isinstance(c, ast.Call):
                    f = c.func
                    if isinstance(f, ast.Name):
                        calls.add(f.id)
                    elif isinstance(f, ast.Attribute):
                        # ⚠ `_rt.load()` contributes `load` — the MODULE is lost. That is why a
                        # cross-module technique is UNKNOWN here rather than confidently absent.
                        calls.add(f.attr)
            out.setdefault(n.name, set()).update(calls)
    return out, ""


def _reach(graph, seeds):
    seen, stack = set(), list(seeds)
    while stack:
        x = stack.pop()
        if x in seen:
            continue
        seen.add(x)
        stack.extend(graph.get(x, ()))
    return seen


def read_paths():
    """Names MINI reaches and ON AIR does not. -> (list[dict] | None, why)"""
    graph, why = _fn_calls(os.path.join(HERE, "control_app.py"))
    if graph is None:
        return None, why
    missing = [e for e in (MINI_ENTRIES + ONAIR_ENTRIES) if e not in graph]
    if missing:
        # ⚠ A SEED THAT NO LONGER EXISTS MEANS THIS WALKED THE WRONG THING. Reporting a tidy
        # "0 gaps" off a graph whose entry points were renamed is the instrument failing quietly.
        return None, ("entry point(s) %s are not in control_app.py any more, so this census "
                      "measured nothing — the stream's shape changed under it" % ", ".join(missing))
    mini, onair = _reach(graph, MINI_ENTRIES), _reach(graph, ONAIR_ENTRIES)
    rows = []
    for name in sorted(mini - onair):
        if name not in graph:
            continue                      # a bare attribute name, not a function in this module
        exempt = NOT_A_TECHNIQUE.get(name)
        rows.append({
            "kind": "read-path",
            "technique": name,
            "reproduced": True if exempt else False,
            "why": (exempt if exempt else
                    "reachable from MINI (%s) and from no ON AIR entry point — if MINI is removed "
                    "this code stops running and nothing else calls it"
                    % ", ".join(sorted(e for e in MINI_ENTRIES if name in _reach(graph, [e])))),
        })
    return rows, ""


#: A template is exercised when a row is journaled with the scene it lives on. ⚠ DERIVED FROM THE
#: ROUTE, not a second table: `reel_templates.ROUTES` already says which container each route reads.
ROUTE_SCENE = {"STASH": ("stash",), "INVENTORY": ("inventory",), "CHRONICLE": ("chronicle",)}

#: Below this many NAME-BEARING rows on a door, a per-scenario count cannot tell "ON AIR does not
#: reach it" from "ON AIR has barely run". Both would read 0. [[zero-needs-a-denominator]]
MIN_ROWS_TO_JUDGE = 30


def _door_rows():
    """Journal rows that carry the stream stamp. -> (dict door -> rows, coverage, why)

    ⚠⚠ `door` ALREADY EXISTS — v2687 put it on every row for exactly this reason, and the first
    draft of this census asserted "no ON AIR session has been recorded" WITHOUT LOOKING. It had
    been recorded: 23 rows. The assertion was wrong and would have shipped as a measurement.
    [[feedback-silence-is-not-evidence]]

    ⚠ AND THE COVERAGE IS THE HEADLINE, NOT THE COUNTS. Measured 2026-09-09: 25 of 3,926 rows carry
    a door at all (0.6%) — the stamp shipped recently and everything older is correctly ABSENT
    rather than guessed. A per-scenario tally over 25 rows cannot answer anything about a stream.
    """
    path = os.environ.get("TV_SESSIONS") or os.path.join(HERE, "sessions.jsonl")
    try:
        import json as _json
        total, by = 0, {}
        with io.open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                total += 1
                try:
                    r = _json.loads(line)
                except Exception:
                    continue
                d = str(r.get("door") or "")
                if d:
                    by.setdefault(d, []).append(r)
    except FileNotFoundError:
        return None, None, ("no journal at %s, so nothing is established about either stream"
                            % os.path.basename(path))
    except Exception as exc:
        return None, None, "the journal could not be read (%s)" % type(exc).__name__
    stamped = sum(len(v) for v in by.values())
    cov = {"stamped": stamped, "total": total,
           "pct": (round(100.0 * stamped / total, 1) if total else None)}
    return by, cov, ""


def _stream_verdict(match, label):
    """Did ON AIR exercise this technique? -> (True | False | None, why)

    ⚠⚠ THREE OUTCOMES AND THE MIDDLE ONE IS THE POINT. `False` is a MEASURED gap over a real
    denominator — actionable. `None` is "the stamped population is too small to tell", which looks
    identical in the data and is the opposite fact. Collapsing them would authorise a removal on
    the strength of a stream that has barely run. [[unknown-stays-unknown]]
    """
    by, cov, why = _door_rows()
    if by is None:
        return None, why
    onair = by.get("onair") or []
    bearing = [r for r in onair if (r.get("names") or r.get("scene") not in (None, "session_end"))]
    hits = [r for r in onair if match(r)]
    if len(bearing) < MIN_ROWS_TO_JUDGE:
        return None, ("only %d of %d ON AIR rows carry a scene at all (%d rows stamped out of "
                      "%d in the journal, %s%%) — far too few to tell 'ON AIR never reaches %s' "
                      "from 'ON AIR has barely run'. Both read 0."
                      % (len(bearing), len(onair), cov["stamped"], cov["total"], cov["pct"], label))
    if hits:
        return True, ("%d ON AIR row(s) exercised %s" % (len(hits), label))
    return False, ("0 of %d name-bearing ON AIR rows reached %s — a measured gap over a real "
                   "denominator" % (len(bearing), label))


def templates():
    """Every route the readers match against. -> (list[dict] | None, why)"""
    try:
        import reel_templates as _rt
        routes = list(getattr(_rt, "ROUTES", ()) or ())
    except Exception as exc:
        return None, ("reel_templates would not import (%s), so which templates exist is UNKNOWN — "
                      "it is NOT 'there are none'" % type(exc).__name__)
    if not routes:
        return None, "reel_templates.ROUTES is empty, so this census inspected nothing"
    rows = []
    for r in routes:
        label = str(r[0]) if isinstance(r, (list, tuple)) and r else str(r)
        container = str(r[1]).upper() if isinstance(r, (list, tuple)) and len(r) > 1 else ""
        scenes = ROUTE_SCENE.get(container, ())
        if not scenes:
            rows.append({"kind": "template", "technique": label, "reproduced": None,
                         "why": ("route %r reads container %r, which maps to no known scene, so "
                                 "whether ON AIR exercises it cannot be measured from the journal"
                                 % (label, container))})
            continue
        got, why = _stream_verdict(
            lambda x, _s=scenes: str(x.get("scene") or "") in _s, "the %s template" % label)
        rows.append({"kind": "template", "technique": label, "reproduced": got, "why": why})
    return rows, ""


def scenarios():
    """Every scenario the extractor recognises. -> (list[dict] | None, why)"""
    try:
        import extract_gap as _eg
    except Exception as exc:
        return None, ("extract_gap would not import (%s), so which scenarios exist is UNKNOWN"
                      % type(exc).__name__)
    panel = tuple(getattr(_eg, "PANEL_SCENES", ()) or ())
    floor = tuple(getattr(_eg, "FLOOR_SCENES", ()) or ())
    if not panel or not floor:
        return None, ("extract_gap no longer declares PANEL_SCENES/FLOOR_SCENES, so the scenario "
                      "vocabulary could not be read — UNKNOWN, not empty")
    rows = []
    for name, scenes in (("PANEL", panel), ("FLOOR", floor), ("CHRONICLE", ("chronicle",))):
        got, why = _stream_verdict(
            lambda x, _s=scenes: str(x.get("scene") or "") in _s, "the %s scenario" % name)
        rows.append({"kind": "scenario", "technique": name, "reproduced": got,
                     "why": "%s · recognised from scene(s) %s" % (why, ", ".join(scenes))})
    return rows, ""


def census():
    """The whole census, in one shape. -> dict

    -> {"ok", "rows", "total", "reproduced", "gaps", "unknown", "families", "why"}

    ⚠ `ok` False means a FAMILY could not be read, which is different from a family with gaps. The
    counts are then None rather than a total over the half that answered.
    """
    out = {"ok": False, "rows": [], "total": None, "reproduced": None, "gaps": None,
           "unknown": None, "families": {}, "why": ""}
    whys, rows, broken = [], [], []
    for fam, fn in (("read-path", read_paths), ("template", templates), ("scenario", scenarios)):
        got, why = fn()
        out["families"][fam] = {"ok": got is not None, "n": (None if got is None else len(got)),
                                "why": why}
        if got is None:
            broken.append(fam)
            whys.append("%s: %s" % (fam, why))
            continue
        rows.extend(got)
        if why:
            whys.append("%s: %s" % (fam, why))
    out["rows"] = rows
    if broken:
        out["why"] = ("%d technique family/families could not be read (%s), so the census is "
                      "PARTIAL and its totals are UNKNOWN — not a clean bill: %s"
                      % (len(broken), ", ".join(broken), " · ".join(whys)))
        return out
    _by, _cov, _cw = _door_rows()
    out["doorCoverage"] = _cov if _by is not None else None
    out["doorCoverageWhy"] = _cw or (
        "the stream stamp `door` covers %s of %s journal rows (%s%%) — every technique verdict "
        "below is bounded by that, and it is the first thing to raise before any of the UNKNOWNs "
        "can close" % (_cov["stamped"], _cov["total"], _cov["pct"]) if _cov else "")
    out["ok"] = True
    out["total"] = len(rows)
    out["reproduced"] = sum(1 for r in rows if r["reproduced"] is True)
    out["gaps"] = sum(1 for r in rows if r["reproduced"] is False)
    out["unknown"] = sum(1 for r in rows if r["reproduced"] is None)
    out["why"] = ("%d technique(s): %d reproduced under ON AIR, %d measured gaps, %d never asked"
                  % (out["total"], out["reproduced"], out["gaps"], out["unknown"]))
    return out


def may_unify(rep=None):
    """May MINI be removed yet? -> (bool, why)

    ⚠⚠ FALSE IS THE ONLY SAFE DEFAULT AND IT IS RETURNED ON EVERY DOUBT. A census that could not be
    read must not authorise the removal it exists to gate — that would make an instrument failure
    into permission. His order was "first make sure", and a thing nobody measured is not sure.
    """
    rep = census() if rep is None else rep
    if not rep.get("ok"):
        return False, ("the census could not be completed, so nothing is established about what "
                       "ON AIR reproduces — %s" % rep.get("why", ""))
    if rep["gaps"]:
        names = [r["technique"] for r in rep["rows"] if r["reproduced"] is False]
        return False, ("%d technique(s) run under MINI and under nothing else: %s"
                       % (rep["gaps"], ", ".join(names[:8])))
    if rep["unknown"]:
        names = [r["technique"] for r in rep["rows"] if r["reproduced"] is None]
        return False, ("%d technique(s) have never been checked against ON AIR: %s — an unasked "
                       "question is not a yes" % (rep["unknown"], ", ".join(names[:8])))
    return True, "every technique MINI carries is reproduced under ON AIR"


def main(argv):
    import json
    rep = census()
    if "--json" in argv:
        print(json.dumps(rep, indent=1, sort_keys=True))
        return 0
    if not rep["ok"]:
        print("PARTIAL — %s" % rep["why"])
        return 1
    print("#44 · CAN MINI BE REMOVED? — %s" % rep["why"])
    print("      %s" % (rep.get("doorCoverageWhy") or ""))
    for fam in ("read-path", "template", "scenario"):
        fr = [r for r in rep["rows"] if r["kind"] == fam]
        print("\n  %s (%d)" % (fam.upper(), len(fr)))
        for r in fr:
            mark = {True: "✅", False: "❌", None: "❓"}[r["reproduced"]]
            print("    %s %-38s %s" % (mark, r["technique"][:38], r["why"][:88]))
    ok, why = may_unify(rep)
    print("\n  %s  %s" % ("UNIFY MAY PROCEED" if ok else "⛔ UNIFY IS BLOCKED", why))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
