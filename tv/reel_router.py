#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A7·ROUTE — ONE STATION PER REEL, DERIVED FROM THE REEL'S OWN EVIDENCE.

His ask, 2026-09-05: *"we want a unified logic for all reels no gaps.. they all get run through
the processing system we built where is station and the printer to get filtered through the heart
and console and eventually end up in their individual routes"* and, when I showed him the
measurement: *"the routing system can be placed after the reels get filtered and still end up
where they are. just the gates placed accordingly."*

⚠⚠ THE DEFECT THIS EXISTS FOR, MEASURED 2026-09-05 ON HIS SHELF. 40 reels, 29 with no journal row
at all, and the oldest ten — back to 2026-07-25 — all unread. It is not that the queue is ordered
badly. **There is no queue.**

    chronicle_autoread_tick   takes the 12 NEWEST journal visits and carries an explicit
                              `if v.get("source") == "reel": continue`. Journal-only BY DESIGN.
    vault_autoreel_tick       is the reel reader. It takes `_vault_owed_reels()`, which returns
                              only reels retention tags `vault-owes`. MEASURED: 0 of 40.

`_vault_owed_reels()` is first-match-wins and `vault-owes` is the LAST rule, so every reel matches
something earlier — `zero-pages` 28, `test-fixture` 7, `recent` 5, `vault-owes` **0**. The lane
picks nothing, forever, and publishes `owed: 0`, which reads as a healthy idle lane.

⚠ THE CODE ALREADY SAID SO and filed it as latent: *"The `vault-owes` tag genuinely never fires on
his tree because earlier rules match first. That is a LATENT defect the day a reel legitimately
reaches it."* It is not latent. It is what is starving 29 reels, and it is starving the BIGGEST
ones — unread reels run to 2,387 frames while no reel that WAS read exceeds 134.

⚠⚠ AND THE ROOT IS ONE QUESTION DOING TWO JOBS. `reel_story._stage_of(tag)` derives a reel's
STAGE from the RETENTION TAG, and `printer.stream()`'s route field is literally the tag glued to
the verdict (`"test-fixture@releasable"`). So *do we keep these bytes* and *where is this reel in
the river* are answered by one value. Collapsing them lets the keep-reason silently decide the
read-fate, which is [[unknown-stays-unknown]] §2 — two questions wearing one name. Measured
consequence: all 40 reels sit at TWO of `reel_story`'s six stages (`swept` 28, `releasable` 12);
`filmed`, `triaged`, `banked` and `vault-done` are permanently EMPTY.

WHAT THIS MODULE DOES, AND THE LINE IT WILL NOT CROSS:

  · it assigns exactly ONE station per reel, from the reel's OWN evidence — surveyed, names read,
    sealed — and NEVER from the retention tag. `assert_independent_of_retention()` is the guard.
  · every reel on the shelf gets a station. UNKNOWN is a station, not a gap, and is never folded
    into a working total. The invariant `counts sum to shelf size` is asserted, not hoped for.
  · `owed(station)` orders oldest-first — FIFO, by the reel's own capture clock — because that is
    what he asked for and what the frame counts say is being starved.

⚠⚠ IT ARMS NOTHING AND IT DELETES NOTHING. It publishes a queue; it does not consume one. Wiring
a reader to `owed("STATION")` would start **13 paid sweeps** on his money, and the 2026-08-28
incident was exactly that — a predicate that read as equivalent queued 19 reels where retention
said 2, three of them test fixtures. That wiring is a separate, gated decision and it is HIS.
**The prune stays OFF; this routes and stamps, it never removes.** [[borrowed-surface]]
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

#: The river, in order. A reel's station is its POSITION; what it OWES is the named gate in front
#: of it. Keeping those separate is the whole point — two reels can sit at the same position and
#: owe different work, and one word for both is how `route` became the retention tag.
STATIONS = ("INTAKE", "TRIAGE", "EMPTY", "STATION", "PRINTER", "JOIN", "CAPTURE",
            "ROUTED", "TOMBSTONE")

#: ⚠ NOT a station in the list above, and deliberately so. UNKNOWN means the evidence could not be
#: read — never "nothing was found". It is reported beside the totals and never inside them, so a
#: shelf nobody could measure cannot be mistaken for a shelf with no work waiting.
UNKNOWN = "UNKNOWN"

#: what each station is waiting on. The gate, in his words, "placed accordingly".
OWES = {
    "INTAKE":    "SURVEY — nothing has classified this reel's frames yet",
    "TRIAGE":    "TRIAGE — the template is known and retro_triage has not walked its frames, so "
                 "whether it holds a panel at all is UNSURVEYED, not empty",
    "EMPTY":     "ROUTE — retro_triage walked it IN FULL and found ZERO panel frames, so there is "
                 "no item name in this footage and a paid read would buy nothing. ⚠⚠ THAT IS NOT "
                 "AN EXIT. His question, 2026-09-05: *\"this happens before it even enters the "
                 "printer and station? doesnt it need to be gated after also.\"* Right on both "
                 "counts. A reel with nothing to READ still has a door it came from and still "
                 "owes a stamped tombstone, so it continues down the same river carrying less "
                 "— it does not leave it. And the verdict is REOPENABLE: `panels` is what THIS "
                 "survey's classifier saw, `retro_triage.json` records no classifier version, so "
                 "EMPTY means 'nothing found by the survey of surveyedAt' and never 'nothing is "
                 "there'. (A9's 10-15% law: most footage is a farming run, and that is what "
                 "footage IS, not a fault.)",
    "STATION":   "READ — the survey walked it and found panels, and no item name has ever been "
                 "read from it. THIS is the paid queue.",
    "PRINTER":   "SEAL — the names were read; the session carries no seal to put them in",
    "JOIN":      "JOIN — sealed AND the names are on disk; the seal does not carry them. Code.",
    "CAPTURE":   "CAPTURE, then ROUTE — sealed and the reader yielded nothing. REG-340: D2R "
                 "prints the name only on the character panel, which the reel does not film, so "
                 "this is a capture change and never a paid read. ⚠ Also not an exit: it still "
                 "owes a route and a stamped tombstone like every other reel.",
    "ROUTED":    "TOMBSTONE — the extraction contract is satisfied; it may be released with a stamp",
    "TOMBSTONE": "nothing — it is released, and the stamp is its record",
}

#: ⚠⚠ THE FIELDS A STATION MAY BE DERIVED FROM. Anything outside this set is the keep-reason
#: wearing a disguise. `assert_independent_of_retention()` enforces it by walking THIS module's
#: own AST, because a rule that lives only in a docstring is a rule the next edit will not see.
EVIDENCE_FIELDS = ("sealed", "names", "worthReading", "surveyed")

#: the fields that answer "why are we KEEPING these bytes". Reading any of them to decide a
#: station re-creates the exact defect. Named so the guard can fail on them by name.
RETENTION_FIELDS = ("tag", "funnel", "route", "held", "holdKind", "stage", "stageIdx")


def _captured_ms(reel, hist=None):
    """When this reel was actually filmed. -> (epoch_ms | None, source)

    ⚠⚠ THE FRAMES ARE THE CLOCK — NOT THE ID, AND NOT mtime. His correction, 2026-09-05:
    *"timestamps should be taken care of this though the 13 digit is like a reference id"*. He is
    right and the measurement shows it: `reel_s_1784984019250_95276`'s id says 1784984019250 while
    its FIRST FRAME says 1784984130673 — **111 seconds apart**. The id is stamped when the session
    opens; the frame is stamped when the picture was taken. Only one of those is the capture.

    So this reads `f_<epoch-ms>.jpg` and takes the EARLIEST, which is the recorder's own written
    evidence. `hover_calibration._frames_by_ts` already reads frame names this way, so this is the
    tree's existing convention rather than a second one.

    ⚠ mtime is not a candidate at all: a directory's mtime moves when anything TOUCHES it — a
    survey, a copy, a backup — so ordering by it would put a reel that was merely looked at ahead
    of one filmed months earlier. FIFO has to mean "filmed first".

    ⚠⚠ RETURNS None, NEVER 0, when no clock can be read. A zero is a date in 1970 and would sort
    to the FRONT of a FIFO queue — an unmeasured reel jumping ahead of every measured one, which
    is the failure mode this whole module exists to refuse. The `source` says which clock answered
    (`frames` / `id` / None) so a reel resting on the weaker one is visible rather than assumed.
    [[unknown-stays-unknown]]
    """
    d = os.path.join(hist or _hist_dir(), str(reel or ""))
    best = None
    try:
        for nm in os.listdir(d):
            if not nm.lower().endswith(".jpg"):
                continue
            digits = "".join(ch for ch in os.path.splitext(nm)[0] if ch.isdigit())
            if len(digits) < 13:
                continue
            try:
                ms = int(digits[-13:])
            except ValueError:
                continue
            if best is None or ms < best:
                best = ms
    except Exception:
        best = None
    if best is not None:
        return best, "frames"
    # ⚠ THE FALLBACK IS NAMED, NOT SILENT. A reel whose frames are gone (already pruned, or never
    # written) can still be ordered by its session id — but the caller must be able to see that it
    # is resting on the weaker clock, because the two differ by minutes and the id is an id.
    m = re.search(r"(\d{13})", str(reel or ""))
    if m:
        return int(m.group(1)), "id"
    return None, None


def _hist_dir():
    """Where the reels live. -> path"""
    return (os.environ.get("TV_HIST") or os.path.join(HERE, "frames", "hist"))


def _station_of(ev):
    """The station this evidence puts a reel at. -> (station, why)

    ⚠ IT READS ONLY `EVIDENCE_FIELDS`. No retention tag, no keep-reason, no hold kind. If this
    function ever needs one of those to decide, the two questions have merged again and the guard
    below must fail rather than let it through.
    """
    if ev is None:
        return UNKNOWN, "the printer did not answer for this reel, so its position is unmeasured"
    sealed = ev.get("sealed")
    names = ev.get("names")
    surveyed = ev.get("surveyed")
    worth = ev.get("worthReading")
    # ⚠ None is not False for any of these. A reel whose survey could not be read is UNKNOWN, not
    # un-surveyed — the difference is the whole reason this module exists.
    if sealed is None or names is None:
        return UNKNOWN, ("sealed=%r names=%r — at least one is unmeasured, so no position can be "
                         "honestly assigned" % (sealed, names))
    if surveyed is False:
        return "INTAKE", "on the shelf and nothing has classified its frames"
    # ⚠ THE FURTHER-DOWN-RIVER STATES ARE TESTED FIRST. A reel that has already been read and
    # sealed is past the survey; asking whether it is worth reading would send it BACKWARDS.
    if sealed and names:
        return "JOIN", ("sealed and %d name(s) already read — the names exist and the seal does "
                        "not carry them" % int(names))
    if sealed and not names:
        return "CAPTURE", "sealed and the reader yielded no name at all"
    if names and not sealed:
        return "PRINTER", "%d name(s) read and the session carries no seal" % int(names)
    # ⚠⚠ NOT SEALED AND NO NAMES — and here the SURVEY decides the position, because the survey IS
    # a station on this river and not a flag beside it. His question, 2026-09-05: *"what decides
    # its worth reading or not why doesnt it go through the unified filtering process down the
    # river and through the station and printer."* It does: `worthReading` is
    # `retro_triage.worth_reading()`, which is `bool(panels)` from the full-frame triage pass.
    # My first cut flattened that verdict into a FLAG on one station, so 13 reels sat in a queue
    # of which only 7 could ever yield anything — the position said READ and the river had already
    # said otherwise for six of them. A river verdict belongs in the position.
    if worth is None:
        return "TRIAGE", ("the template is known and retro_triage has not walked its frames, so "
                          "whether it holds a panel is UNSURVEYED — which is not empty")
    if worth is False:
        return "EMPTY", ("retro_triage walked it IN FULL and found zero panel frames — there is "
                         "no item name in this footage, so there is nothing here to read")
    return "STATION", "the survey found panels and no name has ever been read from it"


def _evidence(hist=None):
    """Per-reel evidence from the printer's own walk. -> (dict reel -> ev, why)

    ⚠⚠ `hist` IS ACCEPTED AND CANNOT BE HONOURED, AND SAYING SO IS THE POINT. `printer.stream()`
    takes only `(reel=None)` — it reads whatever shelf its own module resolves. So a caller doing
    `route(hist=<fixture>)` would take CAPTURE CLOCKS from the fixture and STATION EVIDENCE from
    the live shelf, and a fixture test would silently grade his real 40 reels and pass. Two
    independent audits caught this within minutes of each other.
    Rather than accept a parameter that quietly lies, this REFUSES a mismatched `hist` and names
    the supported route: point TV_HIST at the fixture (the tree's own convention), or patch
    `_evidence`. [[feedback-fixtures-never-touch-live-data]] [[plumbing-with-no-tap]]

    ⚠ THE PRINTER IS THE SOURCE and this does not re-derive it. `printer.stream()` already walks
    every reel; building a second walk here would be a second authority on the same question, and
    two authorities disagreeing about "where is this reel" is the defect one station up.
    """
    if hist and os.path.abspath(hist) != os.path.abspath(_hist_dir()):
        return None, ("refusing to mix shelves: hist=%r was passed, but printer.stream() reads "
                      "%r and takes no shelf argument. Set TV_HIST instead, or patch _evidence — "
                      "answering anyway would join this fixture's clocks to the live shelf's "
                      "evidence." % (hist, _hist_dir()))
    try:
        import printer
    except Exception as exc:
        return None, "printer would not import (%s)" % type(exc).__name__
    try:
        rep = printer.stream()
    except Exception as exc:
        return None, "printer.stream() raised (%s)" % type(exc).__name__
    if not rep.get("ok"):
        return None, "printer.stream() could not answer: %s" % str(rep.get("why") or "")[:160]
    # ⚠ WHEN the survey ran, read through retro_triage's own load() and never its file. EMPTY is
    # the verdict of ONE survey at ONE time, and `retro_triage.json` records no classifier
    # version — so without this the report cannot distinguish "nothing is there" from "nothing
    # was found by whatever the classifier was that day". [[stale-reading]]
    # ⚠ `seen_at is None` means THE SURVEY TIMES COULD NOT BE READ — it is not an empty survey.
    # This handler used to hand back `{}` on both the exception and the not-ok path, so every reel
    # then reported `surveyedAt: None` as though the store had been read and held nothing for it.
    # That collapses precisely the distinction the comment above says this exists to preserve.
    seen_at, seen_why = {}, ""
    try:
        import retro_triage as _rt
        blob, ok = _rt.load()
        if ok:
            for k, v in (blob or {}).items():
                seen_at[str(k)] = (v or {}).get("ts")
        else:
            seen_at = None
            seen_why = ("retro_triage.load() reported not-ok, so no survey time could be read for "
                        "any reel — surveyedAt is UNKNOWN, not absent")
    except Exception as exc:
        seen_at = None
        seen_why = ("the retro_triage store would not load (%s) — surveyedAt is UNKNOWN, not "
                    "absent" % type(exc).__name__)
    out = {}
    for row in (rep.get("rows") or []):
        st = row.get("stations") or {}
        ex = st.get("extract") or {}
        tp = st.get("template") or {}
        n = ex.get("names")
        out[str(row.get("reel") or "")] = {
            "sealed": ex.get("sealed"),
            "names": None if n is None else int(n),
            "worthReading": tp.get("worthReading"),
            # a reel the template station could not classify was never surveyed. `say` absent is
            # UNKNOWN-shaped and is passed through as None rather than turned into False.
            "surveyed": None if tp.get("say") is None else True,
            # None here has TWO causes and the report's `why` is what separates them: the store was
            # read and holds no time for this reel, or the store could not be read at all.
            "surveyedAt": None if seen_at is None else seen_at.get(str(row.get("reel") or "")),
        }
    return out, seen_why


def route(hist=None):
    """Every reel on the shelf, with exactly one station each. -> dict

    The invariant is asserted, not assumed: `sum(counts.values()) == shelf` and every reel appears
    exactly once. A router that quietly drops a reel is the gap this was built to close.
    """
    ev, why = _evidence(hist)
    rep = {"ok": False, "stations": list(STATIONS), "owes": dict(OWES),
           "reels": [], "counts": {}, "unknown": 0, "shelf": 0, "why": why}
    if ev is None:
        rep["why"] = "UNKNOWN, not an empty shelf — %s" % why
        return rep
    rows = []
    for reel, e in ev.items():
        station, swhy = _station_of(e)
        ms, src = _captured_ms(reel, hist)
        # ⚠⚠ `e` MAY BE None, AND THIS LINE USED TO CRASH ON IT — found 2026-09-05 by the very
        # sabotage that replaced `reel.route`'s REG-600 axis, on its first real run. `_station_of`
        # opens with `if ev is None: return UNKNOWN, "the printer did not answer for this reel"` —
        # a branch written on purpose, documented, and UNREACHABLE THROUGH ITS ONLY CALLER, which
        # went straight on to `e.get("sealed")` and raised AttributeError. So the module's whole
        # UNKNOWN story ended in a traceback the moment a reel actually went unanswered.
        # The old axis compared two module constants and could never have found it.
        # [[the-unjoined-end]] [[unknown-stays-unknown]]
        _e = e if isinstance(e, dict) else {}
        rows.append({
            "reel": reel,
            "station": station,
            "why": swhy,
            "owes": OWES.get(station),
            "capturedMs": ms,
            "clockFrom": src,
            "sealed": _e.get("sealed"),
            "names": _e.get("names"),
            "worthReading": _e.get("worthReading"),
            "surveyedAt": _e.get("surveyedAt"),
        })
    # FIFO: oldest capture first. ⚠ A reel with NO readable clock sorts LAST, never first — None
    # must not be coerced to 0, because 0 is 1970 and would put every unmeasured reel at the head
    # of the queue ahead of reels whose age is actually known.
    rows.sort(key=lambda r: (r["capturedMs"] is None, r["capturedMs"] or 0, r["reel"]))
    counts = {s: 0 for s in STATIONS}
    unknown = 0
    for r in rows:
        if r["station"] == UNKNOWN:
            unknown += 1
        else:
            counts[r["station"]] += 1
    rep.update({"ok": True, "reels": rows, "counts": counts, "unknown": unknown,
                "shelf": len(rows), "why": ""})
    # ⚠ THE GAP CHECK, and it is the reason this returns a report rather than a list. `counts`
    # excludes UNKNOWN on purpose, so the sum only reconciles when UNKNOWN is added back — which
    # forces any caller printing a total to say how many it could not place.
    rep["reconciles"] = (sum(counts.values()) + unknown) == len(rows)
    # ⚠⚠ POSITION IS NOT THE SAME AS THE BILL, and reporting one number would hide that. 13 reels
    # sit at STATION; the survey says only 7 are WORTH reading. A paid queue built from the
    # position alone would buy six reads the survey already argued against — which is the
    # 2026-08-28 incident's shape exactly. Both numbers are published; neither is folded.
    rep["readable"] = sum(1 for r in rows
                          if r["station"] == "STATION" and r["worthReading"] is True)
    rep["notWorth"] = sum(1 for r in rows
                          if r["station"] == "STATION" and r["worthReading"] is False)
    rep["worthUnknown"] = sum(1 for r in rows
                              if r["station"] == "STATION" and r["worthReading"] is None)
    # ⚠⚠ NAME THE STATIONS NOTHING REACHES, because this module's whole case against
    # `reel_story` was that four of its six stages were permanently empty and nothing said so.
    # A router that silently publishes zeros for its own far end has reproduced the defect it was
    # built to expose. ROUTED and TOMBSTONE are unreached TODAY — nothing routes or tombstones
    # yet (that is gh #210) — and this says so rather than letting a 0 read as "none waiting".
    rep["unreached"] = [st for st in STATIONS if counts.get(st, 0) == 0]
    return rep


def owed(station="STATION", hist=None, limit=None, worth_only=False):
    """The reels waiting at one station, OLDEST FIRST. -> (list, why)

    ⚠⚠ THIS IS A QUEUE, NOT AN INSTRUCTION. Nothing in this module consumes it. Wiring a paid
    reader to `owed("STATION")` would start a sweep per reel on HIS money, and that is his call
    to make with the number in front of him — 2026-08-28 is the precedent: a predicate that read
    as equivalent queued 19 reels where retention said 2, three of them test fixtures.

    ⚠ `worth_only` defaults to FALSE on purpose, so the plain call answers "where is everything"
    rather than silently shrinking the shelf. A PAID caller must pass True and thereby say, at its
    own call site, that it is buying reads — the filter is never applied on its behalf.
    ⚠ True also drops `worthReading is None`: a survey that could not be read is not permission.
    """
    rep = route(hist)
    if not rep.get("ok"):
        return None, rep.get("why") or "the shelf could not be read"
    rows = [r for r in rep["reels"] if r["station"] == station]
    if worth_only:
        rows = [r for r in rows if r["worthReading"] is True]
    return (rows[:limit] if limit else rows), ""


def _string_keys_read_by(fn):
    """Every literal string key `fn` looks up, by AST. -> set

    ⚠⚠ AN AST WALK, NOT A GREP, AND THAT IS NOT PEDANTRY — three guards in this repo have been
    satisfied by their own comments, and one of them matched a comment I had just written about
    the very thing it was checking. Text search cannot tell a rule from a sentence describing the
    rule. [[source-reading-guard]]
    """
    import ast
    import inspect
    import textwrap
    # ⚠ dedent FIRST. `inspect.getsource` on a nested function returns it at its ORIGINAL
    # indentation, which `ast.parse` rejects outright with IndentationError — so the guard would
    # refuse every closure handed to it, including its own RED-proof cases. It fails closed rather
    # than green, which is the right direction, but a guard that cannot read its own subject is
    # measuring nothing. Caught by its own sabotage case. [[feedback-suspect-the-instrument]]
    tree = ast.parse(textwrap.dedent(inspect.getsource(fn)))
    seen = set()
    for node in ast.walk(tree):
        # x.get("k") and x["k"] — both forms, because either would re-couple it
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr == "get" and node.args:
            a = node.args[0]
            if isinstance(a, ast.Constant) and isinstance(a.value, str):
                seen.add(a.value)
        if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant) \
                and isinstance(node.slice.value, str):
            seen.add(node.slice.value)
    return seen


def assert_independent_of_retention():
    """Prove the station is derived from evidence and nothing else. -> (ok, findings)

    ⚠⚠ IT CHECKS BOTH HALVES, because checking only the decider leaves the obvious hole open.
    `_station_of` could stay spotless while `_evidence` quietly copies the retention tag into the
    dict it is handed — the coupling would be back, one function upstream, and a guard aimed only
    at the decider would report clean. That is [[the-unjoined-end]] in reverse: two halves, and
    the guard watching one of them.
    """
    findings = []
    for fn, forbidden, what in (
        (_station_of, RETENTION_FIELDS,
         "decides the station"),
        (_evidence, ("funnel", "route", "tag", "held", "holdKind"),
         "builds the evidence the station is decided from"),
    ):
        try:
            seen = _string_keys_read_by(fn)
        except Exception as exc:
            findings.append("the guard could not parse %s (%s) — that is a REFUSAL, never a pass"
                            % (fn.__name__, type(exc).__name__))
            continue
        if not seen:
            findings.append("the walk found NO string-key reads in %s, which %s. That is an "
                            "instrument failure, not a clean result — a guard that inspects "
                            "nothing reports clean forever. [[feedback-suspect-the-instrument]]"
                            % (fn.__name__, what))
        for f in sorted(seen):
            if f in forbidden:
                findings.append("%s reads %r — the KEEP-REASON reaching the read-fate, which is "
                                "the exact defect this module exists to undo" % (fn.__name__, f))
    return (not findings), findings


def main(argv):
    rep = route()
    print("\nA7·ROUTE — one station per reel, from the reel's own evidence\n")
    if not rep.get("ok"):
        print("  UNKNOWN — %s\n" % rep.get("why"))
        return 2
    for s in STATIONS:
        n = rep["counts"].get(s, 0)
        if n or "-v" in argv:
            print("  %-10s %3d   owes %s" % (s, n, OWES.get(s, "")[:78]))
    print("  %-10s %3d   %s" % (UNKNOWN, rep["unknown"],
                                "position unmeasured — never folded into a total"))
    print("\n  shelf %d · reconciles %s" % (rep["shelf"], rep["reconciles"]))
    if rep.get("unreached"):
        print("  UNREACHED (nothing is at these — a 0 here is not 'none waiting'): %s"
              % ", ".join(rep["unreached"]))
    print("  at STATION: %d worth reading · %d the survey argues against · %d survey unreadable"
          % (rep["readable"], rep["notWorth"], rep["worthUnknown"]))
    q, _ = owed("STATION", limit=5, worth_only=True)
    if q:
        print("\n  the READ queue, oldest first (nothing consumes it — a queue, not an arming):")
        for r in q:
            print("    %-34s captured=%d names=%s sealed=%s"
                  % (r["reel"][:34], r["capturedMs"], r["names"], r["sealed"]))
    ok, findings = assert_independent_of_retention()
    print("\n  independent of the keep-reason: %s" % ("YES" if ok else "NO"))
    for f in findings:
        print("    ✗ %s" % f)
    print()
    return 0 if (rep["reconciles"] and ok) else 1


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
