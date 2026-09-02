"""A21c — THE ROSTER ROUTES, on the same heart, judged by the same corroborator.

Konyo, 2026-09-03: *"connect that roster to the heart of the console too.. everything should be
designed and architecured in that manner"*

WHAT A ROSTER ROUTE IS. A catalog declared in bible.html reaches a screen through a chain, and a
break anywhere makes the number unreadable rather than wrong:

    declared in bible.html  ->  getter on window  ->  probe asks it  ->  total on the wire
        ->  a surface states its unit

The routes are discovered from the `*_roster.json` artifacts on disk, the same way
`chronicle_routes` finds them. A hand-kept table of getters is how `_gSetRoster` sat named in
`control_app.py` for months with no definition on the board. [[the-unjoined-end]]

THE CORROBORATOR IS THE SAME FUNCTION — `chronicle_routes.corroborate`. Not a copy of its rule.
[[copy-drift]]

⚠ JOIN NOT LANDED IN THIS FILE. `heart_state()` / `run_gates.py` are HIS dirty on the v2457 bump.
The join snippet is in the module docstring at the bottom so Claude can land it with that ship.
"""
import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BIBLE = os.path.join(ROOT, "bible.html")

# the heart's four words, imported rather than re-spelled so they can never drift apart
try:
    import chronicle_routes as _CR
    FLOWING, WATCHED, DARK, UNKNOWN = _CR.FLOWING, _CR.WATCHED, _CR.DARK, _CR.UNKNOWN
except Exception:                          # import failure is UNKNOWN later, not a fifth word
    FLOWING, WATCHED, DARK, UNKNOWN = "FLOWING", "WATCHED", "DARK", "UNKNOWN"

# a roster artifact is a catalog's evidence; these are NOT catalogs
NOT_A_ROUTE = ("chronicle_audit_baseline.json", "vault_corpus_index.json")

LINKS = ("declared", "getter", "probe", "total", "unit")


def _defines(src, name):
    """Is `name` DEFINED on window, or merely mentioned? -> bool

    ⚠ `_gSetRoster` was named in `control_app.py` and in prose for months while no definition
    existed. A mention is the thing this must not count. Match `window.NAME =`, and skip a hit
    that sits after `//` on its own line — a comment reproducing the assignment is still a
    mention. [[source-reading-guard]]
    """
    if not src or not name:
        return False
    rx = re.compile(r"window\.%s\s*=" % re.escape(name))
    for m in rx.finditer(src):
        line_start = src.rfind("\n", 0, m.start()) + 1
        if "//" in src[line_start:m.start()]:
            continue
        return True
    return False


def _decomment_py(s):
    """Strip docstrings and comments from Python source. [[source-reading-guard]]"""
    s = re.sub(r'"""(?:.|\n)*?"""', " ", s)
    s = re.sub(r"'''(?:.|\n)*?'''", " ", s)
    return re.sub(r"(?m)#.*$", " ", s)


def _routes_on_disk():
    """-> [(key, filename)] discovered, never typed."""
    out = []
    try:
        names = os.listdir(HERE)
    except Exception:
        return out
    for p in sorted(names):
        if p.endswith("_roster.json") and p not in NOT_A_ROUTE:
            out.append((p[:-len("_roster.json")], p))
    return out


def _decl_patterns(key):
    """-> [regex] that must hit bible.html for this roster to count as DECLARED.

    Derived from the generators that already name the source lines — not restated here. A
    pattern list typed in this file would be a second copy of `roster_sync.SOURCE_DECLS` and
    would drift the day a declaration is renamed. [[copy-drift]]
    """
    if key in ("unique", "set"):
        try:
            import roster_sync as _rs
            pats = list(getattr(_rs, "SOURCE_DECLS", ()) or ())
        except Exception:
            return []
        if key == "unique":
            return [p for p in pats if "ITEM_VALUE" in p or "_UNI_EXTRA" in p]
        return [p for p in pats if "ITEM_SETS" in p or "SET_PIECES" in p]
    if key == "runeword":
        # build_runeword_roster.extract looks up this exact token; importing the string
        # constant from AST would be heavier than one literal the generator already owns.
        return [r"const\s+RUNEWORDS\s*="]
    return []


def _declared(bible, key):
    """Does bible.html still carry the catalog this roster is generated from? -> bool"""
    pats = _decl_patterns(key)
    if not pats:
        return None                     # no generator to ask — UNKNOWN, never False
    for p in pats:
        try:
            if re.search(p, bible):
                return True
        except re.error:
            return None
    return False


def _defined_getters(bible):
    """Window names that are ASSIGNED, not mentioned."""
    found = set()
    for m in re.finditer(r"window\.([A-Za-z_][A-Za-z0-9_]*)\s*=", bible):
        line_start = bible.rfind("\n", 0, m.start()) + 1
        if "//" in bible[line_start:m.start()]:
            continue
        found.add(m.group(1))
    return found


def _getter_for(key, defined, probe_code=""):
    """Pick the board getter for one roster from names assigned on window AND asked by the probe.

    No table of getters. The conventional `_g{Key}Roster` is tried first; runewords never
    followed it (`_rwTotalN` is the definition that exists). A missing pick is DARK, which
    is the `_gSetRoster` defect this exists to catch the next time.

    ⚠ INTERSECT WITH THE PROBE. A fuzzy `key in name` match accepted `_gSetRosterX` as the
    set getter after a rename sabotage, so the lane stayed FLOWING and the RED proof was
    inert. A definition nobody asks for is not this roster's getter. [[source-reading-guard]]
    """
    if not defined:
        return None
    titled = key[:1].upper() + key[1:]
    conv = "_g%sRoster" % titled
    if conv in defined:
        return conv
    asked = set(re.findall(r"window\.([A-Za-z_][A-Za-z0-9_]*)", probe_code or ""))
    cand = defined & asked if asked else defined
    hits = sorted(n for n in cand if key.lower() in n.lower() and "Roster" in n)
    if len(hits) == 1:
        return hits[0]
    if key == "runeword":
        hits = sorted(n for n in cand if n.startswith("_rw") and "Total" in n
                      and "Paint" not in n)
        if len(hits) == 1:
            return hits[0]
    return None


def _tally_key(key):
    """Artifact stems are singular (`unique`); the wire and the surface are plural (`uniques`)."""
    return key if key.endswith("s") else key + "s"


def _unit_stated(ui, tkey):
    """Does the surface say what the denominator is OVER, with a non-empty word?

    ⚠ `{w: ''}` IS NOT A UNIT. A key present with an empty word is the same defect as no key:
    a right number under an unstated unit. Matching `{w:` alone would have called that healthy.
    """
    if not ui or not tkey:
        return False
    m = re.search(r"%s\s*:\s*\{w:\s*'([^']*)'" % re.escape(tkey), ui)
    return bool(m and m.group(1).strip())


_MEMO = {"key": None, "val": None}


def _source_key():
    try:
        stamps = []
        for p in sorted(os.listdir(HERE)):
            if p.endswith(".py") or p.endswith("_roster.json"):
                stamps.append(os.path.getmtime(os.path.join(HERE, p)))
        for extra in (BIBLE, os.path.join(HERE, "control_ui.html"),
                      os.path.join(HERE, "control_app.py")):
            if os.path.isfile(extra):
                stamps.append(os.path.getmtime(extra))
        return (len(stamps), round(max(stamps), 3) if stamps else 0)
    except Exception:
        return None


def routes(tally=None, bible=None, probe=None, ui=None):
    """-> dict, in the heart's four words.

    `tally` is the live per-lane payload when one is available; without it the `total` link is
    UNKNOWN, never absent. `bible` / `probe` / `ui` let a test sabotage a copy in memory — this
    module must never write bible.html to prove it can go red.
    """
    injected = any(x is not None for x in (bible, probe, ui))
    _k = None if injected else _source_key()
    if _k is not None:
        _k = (_k, tuple(sorted((k, (v or {}).get("total"))
                               for k, v in (tally or {}).items()))
              if isinstance(tally, dict) else None)
    if _k is not None and _MEMO["key"] == _k and _MEMO["val"] is not None:
        return _MEMO["val"]

    if bible is None:
        try:
            with io.open(BIBLE, encoding="utf-8", errors="replace") as fh:
                bible = fh.read()
        except Exception as e:
            return {"ok": False, "routes": [], "counts": None, "flags": [],
                    "why": "bible.html could not be read (%s), so the routes are UNKNOWN"
                           % str(e)[:70]}
    if probe is None:
        try:
            with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8",
                         errors="replace") as fh:
                probe = fh.read()
        except Exception as e:
            return {"ok": False, "routes": [], "counts": None, "flags": [],
                    "why": "the probe source could not be read (%s)" % str(e)[:70]}
    if ui is None:
        try:
            with io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8",
                         errors="replace") as fh:
                ui = fh.read()
        except Exception:
            ui = ""

    probe_code = _decomment_py(probe)
    defined = _defined_getters(bible)
    disk = _routes_on_disk()
    if not disk:
        return {"ok": False, "why": "no *_roster.json artifacts found — the routes cannot be "
                                    "derived, which is UNKNOWN rather than 'no rosters'",
                "routes": [], "counts": {}, "flags": []}

    out = []
    for key, fn in disk:
        tkey = _tally_key(key)
        decl = _declared(bible, key)
        getter = _getter_for(key, defined, probe_code)
        has_getter = bool(getter) and _defines(bible, getter)
        asked = bool(getter) and (("window.%s" % getter) in probe_code)
        tot = None
        if tally is not None:
            p = (tally or {}).get(tkey)
            tot = bool(isinstance(p, dict) and isinstance(p.get("total"), int)
                       and p["total"] > 0)
        unit = _unit_stated(ui, tkey)

        lanes = {
            "declared": {"ok": decl, "by": _decl_patterns(key)[:3]},
            "getter":   {"ok": has_getter, "by": [getter] if getter else []},
            "probe":    {"ok": asked, "by": ["control_app.py"]},
            "total":    {"ok": tot, "by": [tkey + "Total"]},
            "unit":     {"ok": unit, "by": ["control_ui.html"]},
        }

        if decl is None:
            state, why = UNKNOWN, ("no generator named the source lines for %s, so whether it "
                                   "is still declared cannot be told" % key)
        elif not decl:
            state, why = DARK, ("bible.html no longer carries the catalog %s is generated from "
                                "— the artifact is a photograph of a page that moved" % key)
        elif not has_getter:
            state, why = DARK, ("the catalog is declared and no getter exposes it on window, so "
                                "the probe can only ever ask for a function that does not exist")
        elif not asked:
            state, why = DARK, ("the board can answer and nothing asks it — the value exists "
                                "and never reaches a screen")
        elif tot is None:
            state, why = UNKNOWN, ("the board defines it and the probe asks for it; whether a "
                                   "total actually arrives can only be told from a live read, "
                                   "and none was taken")
        elif not tot:
            state, why = DARK, ("the getter exists and the probe asks, and the wire still "
                                "carried no total — the break is between them")
        elif not unit:
            state, why = WATCHED, ("it reports a denominator and the surface never says what "
                                   "that denominator is OVER — a right number under an unstated "
                                   "unit")
        else:
            state, why = FLOWING, ("declared, exposed, asked, reported, and the screen says "
                                   "what it is counting")
        out.append({"key": key, "artifact": fn, "state": state, "why": why, "lanes": lanes,
                    "count": ((tally or {}).get(tkey) or {}).get("total") if tally else None})

    try:
        import chronicle_routes as _cr
        flags = _cr.corroborate(out)
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
    # ⚠ HIS CONSOLE IS HEBREW (cp1255) AND CANNOT ENCODE THE ARROWS THIS PRINTS.
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    import json
    import sys
    t = None
    if len(sys.argv) > 1 and sys.argv[1] == "--live":
        sys.path.insert(0, HERE)
        import control_app as ca
        t = ca._tally_cached()
    d = routes(t)
    print("ROSTER ROUTES — %s" % (d.get("why") or "derived"))
    for r in d.get("routes") or []:
        print("\n  %-10s %-8s n=%s" % (r["key"], r["state"], r["count"]))
        for ln in LINKS:
            v = r["lanes"][ln]
            mark = "OK " if v["ok"] else ("?? " if v["ok"] is None else "-- ")
            by = v.get("by") or []
            print("      %s%-9s %s" % (mark, ln, ", ".join(str(x) for x in by) or "nothing"))
        print("      -> %s" % r["why"])
    print("\n  counts: %s" % d.get("counts"))
    for f in d.get("flags") or []:
        print("  ⚑ %s" % f["say"])

# JOIN FOR CLAUDE (do not land while control_app.py / run_gates.py are HIS):
#   heart_state() -> "rosters": roster_route_state()
#   roster_route_state mirrors fleet_route_state, giving _tally_cached() to routes().
#   Gate("test_roster_routes", [sys.executable, os.path.join(HERE, "test_roster_routes.py")], 180,
#        why="a roster declared in bible.html with no getter, or a getter with no unit, is how
#             the set denominator sat null while its two siblings answered.")
