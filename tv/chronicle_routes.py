"""A21c — THE CHRONICLE ROUTES, derived, in the heart's own vocabulary.

Konyo, 2026-09-02: *"connect it all to the heart of the console.. the chronicles routes should
also be there.. the sets and the uniques espeically.. reverse engineered like the routes and lanes
here also for accuracy going forward when a chronicle is found and read and alayzed even this basic
code is logic that needs to be accurate for the other systems to be correct and learn from
eachother.. when 10 are the same logic obviously one isnt its flagged.. by corrobarator and all."*

WHAT A CHRONICLE ROUTE IS. A name on a Chronicle page reaches his ledger through a chain, and each
link is a LANE:

    bible.html declaration  ->  generator  ->  roster artifact  ->  freshness check  ->  resolver

`heart.vessels()` already speaks FLOWING / WATCHED / DARK / UNKNOWN about background loops. This
says the same four words about the chronicle routes, so one vocabulary covers both — which is the
whole point of his ask, and the reason this does not invent a fifth status word.

⚠ THIS MODULE DERIVES. It does not carry a table of what the routes are, because a hand-kept table
is exactly the thing that goes wrong quietly: the roster it forgets is the roster nobody watches.
The routes are discovered from the `*_roster.json` artifacts on disk, so a chronicle added tomorrow
appears here without anyone remembering to add it. [[the-unjoined-end]] [[unknown-stays-unknown]]

THE CORROBORATOR RULE, which is his sentence made runnable: the routes are siblings and should have
the same lane shape. A lane present on a MAJORITY of routes and missing from one is not a matter of
taste — it is flagged, with the siblings named, so the odd one out has to justify itself.

⚠ WHAT IT FOUND ON ITS FIRST RUN, and the reason it exists: `runeword_roster.json` is hash-stamped
at write time by `build_runeword_roster.py` and **nothing on this machine ever checks that stamp
again**. Its siblings both do — `roster_sync.is_stale()` is called by a gate in `test_control.py`.
So the runeword route was DARK: correct today (measured in sync, 105/105, hash equal), and nothing
would say a word on the day it stopped being. That is not a bug report about a wrong number; it is
a lane with no watcher, which reads as fine and is worse.
"""
import io
import json
import os
import re
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


HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BIBLE = os.path.join(ROOT, "bible.html")

# the heart's four words, imported rather than re-spelled so they can never drift apart
FLOWING, WATCHED, DARK, UNKNOWN = "FLOWING", "WATCHED", "DARK", "UNKNOWN"

# a roster artifact is a chronicle route's evidence; these are NOT chronicles and must not be
# mistaken for one — they are caches, indexes and audit notes that happen to end in the same word.
NOT_A_ROUTE = ("chronicle_audit_baseline.json", "vault_corpus_index.json")

LANES = ("source", "generator", "artifact", "freshness", "resolver")


def _decomment_py(s):
    """Strip docstrings and comments from Python source. [[source-reading-guard]]

    ⚠ Every prose block in this repo names the very identifiers a reference check looks for — this
    file's own header names `runeword_roster.json`, `is_stale` and `build_runeword_roster`. A grep
    over raw text would find them and report a lane that does not exist.
    """
    s = re.sub(r'"""(?:.|\n)*?"""', " ", s)
    s = re.sub(r"'''(?:.|\n)*?'''", " ", s)
    return re.sub(r"(?m)#.*$", " ", s)


def _py_files():
    out = {}
    for p in sorted(os.listdir(HERE)):
        if not p.endswith(".py"):
            continue
        try:
            out[p] = _decomment_py(io.open(os.path.join(HERE, p), encoding="utf-8",
                                           errors="replace").read())
        except Exception:
            continue                      # unreadable is UNKNOWN about that file, not about a lane
    return out


def _routes_on_disk():
    """-> [(key, filename)] discovered, never typed."""
    out = []
    for p in sorted(os.listdir(HERE)):
        if p.endswith("_roster.json") and p not in NOT_A_ROUTE:
            out.append((p[:-len("_roster.json")], p))
    return out


#: What each chronicle's source must still declare for `source` to mean anything. Kept beside the
#: lane it serves; a route with no entry gets the honest existence-only answer and says so.
_SOURCE_TOKENS = {
    "runeword": ("const RUNEWORDS",),
    "set": ("ITEM_SETS", "SET_PIECES_EXTRA"),
    "unique": ("ITEM_VALUE",),
}


def _source_ok(key):
    """Does bible.html still CARRY this chronicle's source, not merely exist? -> bool | None"""
    if not os.path.isfile(BIBLE):
        return False
    toks = _SOURCE_TOKENS.get(key)
    if not toks:
        return None          # no token declared for this route — UNKNOWN, never a bare True
    try:
        s = io.open(BIBLE, encoding="utf-8", errors="replace").read()
    except Exception:
        return None          # unreadable is UNKNOWN, not absent
    return any(t in s for t in toks)


def _artifact_lane(fn):
    """The roster itself: does it exist, what does it hold, what does it claim about its source."""
    path = os.path.join(HERE, fn)
    if not os.path.isfile(path):
        return {"ok": False, "why": "no artifact on disk", "count": None, "stamp": None}
    try:
        doc = json.load(io.open(path, encoding="utf-8"))
    except Exception as e:
        # a roster that will not parse is UNKNOWN, never empty — an empty roster resolves nothing
        # and would read as "this chronicle has no names", which is a different and false claim.
        return {"ok": None, "why": "artifact will not parse — %s" % str(e)[:60],
                "count": None, "stamp": None}
    n = doc.get("count")
    if n is None:
        for k in ("pieceCount", "setCount"):
            if doc.get(k) is not None:
                n = doc.get(k)
                break
    return {"ok": True, "why": "", "count": n, "stamp": (doc.get("sourceHash") or None)}


def _mentions(files, needle, also=None):
    """-> sorted filenames whose CODE (not prose) names `needle`, optionally near `also`."""
    hits = []
    for name, code in files.items():
        if needle not in code:
            continue
        if also and not re.search(also, code):
            continue
        hits.append(name)
    return sorted(hits)


def _comparators():
    """-> {module.func: [roster artifacts it covers]} — functions that COMPARE a stamped hash
    against a recomputed one.

    ⚠⚠ THE FIRST CUT OF THIS FILE GOT BOTH VERDICTS BACKWARDS, and only a measurement taken by
    hand ten minutes earlier caught it. It asked "does a file name this roster AND the word
    sourceHash", which is true of the WRITER that stamps the hash — so `runeword` was reported
    FLOWING when its writer contains no comparison at all. And it asked the gate to name the
    artifact, when the real gate calls `roster_sync.is_stale()` and never says `unique_roster` —
    so the one genuinely gated route was reported ungated. Two inverted answers from one wrong
    question. [[the-unjoined-end]] [[source-reading-guard]] [[feedback-suspect-the-instrument]]

    STAMPING IS NOT CHECKING. Writing a hash into a file produces evidence; comparing it later is
    the lane. This asks the AST for the second thing: a function whose body holds a `==`/`!=`
    against something hash-shaped. AST also settles the comment problem for free — prose is not in
    the tree, so this file's own header cannot satisfy it.
    """
    import ast
    out = {}
    me = os.path.basename(__file__)
    for p in sorted(os.listdir(HERE)):
        if not p.endswith(".py"):
            continue
        if p == me:
            # ⚠⚠ THE DESCRIBER IS NOT A WATCHER, and this module qualified as one. It names every
            # roster artifact and reads `sourceHash`, so the scan found ITSELF and reported the
            # runeword route as watched — by the very code whose only job is to say whether
            # anything watches it. A green produced by the observer is the emptiest green there
            # is. Excluding self is not cosmetic; without it this file can never report a DARK
            # route at all. [[the-unjoined-end]] [[feedback-blind-fixture-green-gate]]
            continue
        try:
            raw = io.open(os.path.join(HERE, p), encoding="utf-8", errors="replace").read()
        except Exception:
            continue                    # unreadable is UNKNOWN about that file, not a verdict
        if "sourceHash" not in raw:
            continue                    # cheap gate first — most of this directory is irrelevant
        try:
            tree = ast.parse(raw)
        except Exception:
            continue
        # ⚠ COVERAGE COMES FROM STRING CONSTANTS, NOT FROM THE TEXT. A regex over raw source read
        # `build_runeword_roster.py`'s own module docstring — which names `set_roster.json` and
        # `unique_roster.json` while explaining itself — and concluded its comparator covered all
        # three routes. My prose vouched for a lane that does not exist, for the third time in
        # this repo. A path constant is a path; a sentence about a path is not.
        # [[source-reading-guard]] [[feedback-comments-vs-code]]
        docstrings = set()
        for holder in ast.walk(tree):
            if isinstance(holder, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                body = getattr(holder, "body", None) or []
                if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                    docstrings.add(id(body[0].value))
        rosters = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstrings:
                rosters.update(re.findall(r"\b([a-z_]+_roster)\.json", node.value))
        rosters = sorted(rosters)
        if not rosters:
            continue
        lines = raw.splitlines(True)
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            end = getattr(node, "end_lineno", None)
            if not end:
                continue
            # ⚠ line-slice, NOT ast.get_source_segment per node. The first version called
            # get_source_segment once per Compare node across a 25,000-line test file and pinned a
            # core until it was killed by PID — the same shape as the unbounded search that once
            # ran for 28 hours here. A cheap slice answers the same question.
            seg = "".join(lines[node.lineno - 1:end])
            if "sourceHash" not in seg:
                continue
            if not any(isinstance(c, ast.Compare) for c in ast.walk(node)):
                continue                # STAMPING IS NOT CHECKING — a writer holds no comparison
            if "json.dump" in seg and "stale" not in seg.lower():
                continue                # it writes the stamp; it does not re-read it
            out["%s.%s" % (p[:-3], node.name)] = rosters
    return out


def _callers(targets):
    """-> {"module.func": [files that CALL it]} — resolved through imports, not grepped.

    ⚠ THE THIRD REACH FAILURE IN THIS ONE INSTRUMENT, and the tell each time was a lane reported
    absent that I had already measured present by hand. The gate for the new runeword check writes
    `import build_runeword_roster as B` and then `B.is_stale()`. A regex for
    `build_runeword_roster.is_stale(` never fires, and a bare `is_stale(` is excluded by its own
    leading dot — so a gate that demonstrably runs read as no gate at all. An alias is invisible to
    text and obvious to the tree. [[source-reading-guard]] [[the-unjoined-end]]
    """
    import ast
    want = {}
    for t in targets:
        mod, _, func = t.partition(".")
        want.setdefault(mod, {})[func] = t
    out = {}
    for p in sorted(os.listdir(HERE)):
        if not p.endswith(".py"):
            continue
        try:
            tree = ast.parse(io.open(os.path.join(HERE, p), encoding="utf-8",
                                     errors="replace").read())
        except Exception:
            continue
        alias, direct = {}, {}          # local name -> module ; local name -> "mod.func"
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                for a in n.names:
                    if a.name in want:
                        alias[a.asname or a.name] = a.name
            elif isinstance(n, ast.ImportFrom):
                if n.module in want:
                    for a in n.names:
                        if a.name in want[n.module]:
                            direct[a.asname or a.name] = want[n.module][a.name]
        for n in ast.walk(tree):
            if not isinstance(n, ast.Call):
                continue
            f = n.func
            if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name):
                mod = alias.get(f.value.id)
                if mod and f.attr in want.get(mod, {}):
                    out.setdefault(want[mod][f.attr], set()).add(p)
            elif isinstance(f, ast.Name) and f.id in direct:
                out.setdefault(direct[f.id], set()).add(p)
    return {k: sorted(v) for k, v in out.items()}


#: Envelope fields that are NOT lanes and must not enter a memo key. `at` is a fresh timestamp on
#: every read, so folding it in would change the key every call and the memo would never hit once.
TALLY_ENVELOPE_SKIP = ("at",)


def tally_memo_key(tally):
    """A hashable fingerprint of a live tally, tolerant of EVERY value shape. -> tuple | None

    ⚠ THE TALLY IS AN ENVELOPE, NOT A MAP OF LANES, and assuming otherwise took two surfaces down.
    Measured on his console: 8 keys, of which only three are lanes —
        runewords/sets/uniques -> {have, total}
        ok (bool) · why (None) · at (int) · source (str) · profile (str)
    Both fleet_routes and roster_routes folded every value with `(v or {}).get("total")` and raised
    on the first scalar they met, so `routes()` failed for every real call and the heart printed
    the exception where the lanes belong. fleet_routes was fixed in v2473; roster_routes was not,
    because I fixed the file in front of me instead of sweeping the shape. The review found it.

    Lanes contribute their `total`; scalars contribute themselves; anything unhashable contributes
    its repr. A cache key is the last place a crash should come from — this one took two panels
    down with it. `profile` is deliberately INCLUDED: main and ladder are different answers, and
    serving one for the other is the ladder scar. [[unknown-stays-unknown]] [[sweep-dont-ask]]
    """
    if not isinstance(tally, dict):
        return None
    out = []
    for k in sorted(tally):
        if k in TALLY_ENVELOPE_SKIP:
            continue
        v = tally[k]
        if isinstance(v, dict):
            out.append((k, v.get("total")))
        else:
            try:
                hash(v)
                out.append((k, v))
            except Exception:
                out.append((k, repr(v)[:80]))
    return tuple(out)


def corroborate(rows):
    """-> [flag]. His sentence, made runnable: *"when 10 are the same logic obviously one isnt
    its flagged.. by corrobarator and all"*.

    The chronicle routes are siblings. A lane that a MAJORITY of them carry and one does not is
    not a matter of taste — it is named, with the siblings listed, so the odd one out has to
    justify itself instead of being noticed later by him.

    ⚠ MAJORITY, NOT UNANIMITY-MINUS-ONE. With two routes and one lacking a lane there is no
    majority and nothing is flagged — two disagreeing is a coincidence, which is the same floor
    `carving-skill` uses for scars. Flagging at 1-vs-1 would make the first route added to a new
    lane look like the broken one.

    ⚠ IT FLAGS, IT NEVER BLOCKS. Standing rule in this console: a lock is a stamp. Nothing here
    returns a verdict anything is allowed to act on.
    """
    flags = []
    # ⚠ THE LANES COME FROM THE ROWS, NOT FROM THIS MODULE'S CONSTANT. The first cut looped over
    # `LANES` — the CHRONICLE lane names — so when `fleet_routes` handed it rows whose lanes are
    # getter/probe/total/unit it compared five names none of those rows carried, found nothing on
    # every one, and returned an empty flag list. It read exactly like "no divergence" and was
    # "I was looking somewhere else". Its own guard caught it, which is the only reason this is a
    # comment and not a shipped false green. [[the-unjoined-end]] [[feedback-suspect-the-instrument]]
    seen, order = set(), []
    for r in rows:
        for k in (r.get("lanes") or {}):
            if k not in seen:
                seen.add(k)
                order.append(k)
    for lane in order:
        have = [r["key"] for r in rows if r["lanes"].get(lane, {}).get("ok")]
        lack = [r["key"] for r in rows if not r["lanes"].get(lane, {}).get("ok")]
        if have and lack and len(have) > len(lack):
            for k in lack:
                flags.append({"route": k, "lane": lane, "siblings": have,
                              "say": "%s has no %s lane while %s do. Ten of the same logic and one "
                                     "that is not is the thing worth looking at — that is why this "
                                     "is flagged rather than left to be noticed."
                                     % (k, lane, " and ".join(have))})
    # the enforcement half of the same rule: a check nobody runs is a check in name only
    enf = [r["key"] for r in rows if r["lanes"].get("freshness", {}).get("enforced")]
    unenf = [r["key"] for r in rows if r["lanes"].get("freshness", {}).get("ok")
             and not r["lanes"]["freshness"].get("enforced")]
    if enf and unenf and len(enf) > len(unenf):
        for k in unenf:
            flags.append({"route": k, "lane": "freshness/enforced", "siblings": enf,
                          "say": "%s has a freshness check that no gate runs, while %s are gated."
                                 % (k, " and ".join(enf))})
    return flags


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
        # ⚠⚠ BIBLE GETS ITS OWN SLOT, NOT JUST A SEAT IN max(). The counts come from bible.html
        # now, and `max` is a LOSSY digest: it cannot tell "bible changed" from "bible did not
        # change" whenever some .py in this directory carries a newer mtime. A real edit usually
        # moves max too — it stamps mtime to now — but a key that CAN collapse two different
        # states into one value is a false equality waiting for the day it matters, and the day it
        # matters here is the day he changes a ruling and the panel keeps printing the old total.
        # Measured: bumping bible.html's mtime left the old key byte-identical.
        # [[stale-reading]] [[unknown-stays-unknown]]
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


def routes():
    """-> dict. Every chronicle route, its lanes, and the sibling divergences.

    ⚠ NOTHING HERE IS ENFORCED. A flagged route is a route with something owed, badged and
    explained. The console must keep working exactly as it did — his standing rule that a lock is a
    stamp and never a gate applies to these routes too.
    """
    _k = _source_key()
    if _k is not None and _MEMO["key"] == _k and _MEMO["val"] is not None:
        return _MEMO["val"]

    files = _py_files()
    comps = _comparators()
    callers = _callers(comps)
    disk = _routes_on_disk()
    if not disk:
        return {"ok": False, "why": "no *_roster.json artifacts found — the routes cannot be "
                                    "derived, which is UNKNOWN rather than 'no chronicles'",
                "routes": [], "counts": {}, "flags": []}

    out = []
    for key, fn in disk:
        art = _artifact_lane(fn)
        stem = fn[:-len(".json")]

        # GENERATOR — who writes it. A roster nobody can regenerate is frozen, not maintained.
        gen = _mentions(files, stem, also=r'"w"|\bwrite\b|json\.dump')
        # FRESHNESS — who ever asks whether the stamp still MATCHES the page. A comparator that
        # covers this roster, found by AST; the writer that stamps it does not count.
        # ⚠ ON THE STEM, NOT THE FILENAME. The comparator index keys on `unique_roster`
        # and this once asked for `unique_roster.json` — every membership test answered
        # False and all three routes reported DARK, including the two that are genuinely
        # gated. A units mismatch reads exactly like an absence. [[label-outlived-referent]]
        fresh = sorted(fn_ for fn_, covers in comps.items() if stem in covers)
        # ENFORCED — reachability follows the CALL, not the artifact's name. The gate says
        # `roster_sync.is_stale()`; it has never once said `unique_roster`.
        enforced = sorted(set("%s -> %s" % (t, fn_) for fn_ in fresh
                              for t in callers.get(fn_, ()) if t.startswith("test_")))
        # RESOLVER — who reads it to answer "which chronicle is this name from".
        res = _mentions(files, stem)

        lanes = {
            # ⚠⚠ EXISTENCE IS NOT CONTENT, AND HARD MODE PROVED IT. This was
            # `bool(os.path.isfile(BIBLE))`, so a bible.html EMPTIED TO ZERO BYTES read as a
            # perfectly healthy source on all three chronicle routes — measured by
            # tv/route_wilson.py, which leaves the file in place and removes what is inside it.
            # A file getting emptied or truncated is far commoner than a file being deleted, so
            # this lane was blind to the failure it is most likely to meet. It now asks whether
            # the source still carries the declaration this route is generated FROM.
            "source": {"ok": _source_ok(key), "by": ["bible.html"]},
            "generator": {"ok": bool(gen), "by": gen},
            "artifact": {"ok": art["ok"], "by": [fn], "count": art["count"],
                         "stamp": (art["stamp"] or "")[:12] or None},
            "freshness": {"ok": bool(fresh), "by": fresh, "enforced": enforced},
            "resolver": {"ok": bool(res), "by": res[:6]},
        }

        # ── the heart's four words, and the rule that keeps two of them apart ──────────────────
        if art["ok"] is None or not os.path.isfile(BIBLE):
            state, why = UNKNOWN, "the route could not be read, which is not the same as absent"
        elif not lanes["generator"]["ok"] or not art["ok"]:
            state, why = DARK, ("nothing can regenerate this roster — it is frozen at whatever it "
                                "held the day it was written, and the page can move under it")
        elif not lanes["freshness"]["ok"]:
            state, why = DARK, ("it is stamped with the source it came from and NOTHING ever "
                                "checks that stamp again — correct today says nothing about "
                                "tomorrow, and no one would be told")
        elif not enforced:
            state, why = WATCHED, ("a freshness check exists but no gate runs it, so the watcher "
                                   "has never had to refuse anything — work owed, not a fault")
        else:
            state, why = FLOWING, ("generated, stamped, and a gate re-checks the stamp against "
                                   "the page")
        # ⚠⚠ THE COUNT COMES FROM THE ONE PRODUCER, NOT FROM THIS LANE'S OWN READING. Until v2484
        # the three route sets each read a different source and the heart showed runeword 105 / 99
        # / 99 and unique 398 / 403 / 403 — every number right, and the panel reading as a
        # contradiction. His ruling: "sync and match them obivously.. no reason to have this gap".
        # This lane's own number is kept beside it, never dropped, and route_totals.disagreements()
        # says so out loud if the two ever differ. [[copy-drift]] [[unknown-stays-unknown]]
        out.append({"key": key, "artifact": fn, "state": state, "why": why, "lanes": lanes,
                    "count": _rt.total(key),
                    # the UNIT travels with the number, from the same producer. Sets count PIECES
                    # and the other two count entries; a section-wide noun could not say that, and
                    # a wrong unit is how "135 names" once meant 135 set pieces.
                    "noun": _rt.noun(key),
                    "artifactCount": art["count"]})

    flags = corroborate(out)
    flags = list(flags) + _rt.disagreements(out, own_field="artifactCount")

    counts = {FLOWING: 0, WATCHED: 0, DARK: 0, UNKNOWN: 0}
    for r in out:
        counts[r["state"]] = counts.get(r["state"], 0) + 1
    _out = {"ok": True, "why": "", "routes": out, "counts": counts, "flags": flags}
    if _k is not None:
        _MEMO["key"], _MEMO["val"] = _k, _out
    return _out


if __name__ == "__main__":
    # ⚠ HIS CONSOLE IS HEBREW (cp1255) AND CANNOT ENCODE THE ARROWS THIS PRINTS.
    # Without this the failure lands in the dangerous direction: a CORRECT tree
    # reports FAILURE while merely REPORTING, which teaches people to ignore the
    # tool — and the pre-push gate caught exactly that on this file.
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    d = routes()
    print("CHRONICLE ROUTES — %s" % (d["why"] or "derived from disk"))
    for r in d.get("routes", []):
        print("\n  %-10s %-8s n=%s" % (r["key"], r["state"], r["count"]))
        for ln in LANES:
            v = r["lanes"][ln]
            mark = "OK " if v["ok"] else ("?? " if v["ok"] is None else "-- ")
            print("      %s%-10s %s" % (mark, ln, ", ".join(v.get("by") or []) or "nothing"))
        print("      -> %s" % r["why"])
    print("\n  counts: %s" % d.get("counts"))
    for f in d.get("flags", []):
        print("  ⚑ %s" % f["say"])
