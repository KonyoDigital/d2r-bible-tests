#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""THE READ SIDE OF THE SHADOW LOG — board #188.

`tv/g5_grok_eyes.py::g5_shadow_log()` writes one JSON line per two-lane vision read:

    {"ts": ..., "image": ..., "claude_names": [...], "grok_names": [...],
     "claude_scene": "...", "grok_scene": "..."}

Those four lane keys occur at exactly FOUR lines tree-wide and ALL FOUR ARE WRITES. Nothing has
ever opened the file. Measured on his live store the day this module was written (6,082 rows,
2026-08-23 23:06:14 -> 2026-09-14 18:05:20): of the 1,596 rows where BOTH lanes answered,
1,079 (67.6%) carried different NAME lists and 968 (60.7%) a different SCENE — while
`tv/g5_grok_eyes.state` read {"on": true, "mode": "primary"}.

**The promotion to primary rests on evidence nobody has ever looked at.** This module is the
reader. It resolves nothing.

WHAT THIS MODULE REFUSES TO DO
------------------------------
1. It never prefers a lane. There is no "correct" column, no winner, no truth. Every divergence is
   published from BOTH sides with its reach, and `reduce_rows` is SYMMETRIC by construction: swap
   the two lanes in the input and the agree/disagree figures are identical while the one-sided
   counts trade places. A disagreement rate this high is a finding about the INSTRUMENTS, and the
   first question it raises is whether the two lanes were even asked the same question — not which
   one to believe.
2. No figure is published without its denominator and its window. Every number this module emits
   is a `figure()` dict carrying n, d, pct, first_ts and last_ts together, and `pct` is None — not
   0.0 — when d is 0. "67.6%" on its own is the kind of confident number this repo refuses.
   [[zero-needs-a-denominator]] [[unknown-stays-unknown]]
3. Rows where only ONE lane answered are not disagreements. They are one-sided, counted in their
   own bucket per lane, and excluded from the agreement denominator. Rows where NEITHER answered
   are not evidence at all. The four buckets partition the input exactly, and that is asserted.
4. It states what the record CANNOT say. The written record carries no per-lane confidence, mode
   or error, so a lane's `[]` cannot be told apart from a lane whose read failed and logged the
   EMPTY sentinel (tv_diablo.py's `_maybe_genius(...) or EMPTY`, whose names is `[]`). That caveat
   is DERIVED from the keys actually present in the rows, so it disappears by itself if the write
   side ever starts carrying them. [[unknown-stays-unknown]]

AN EMPTY LIST IS AN ANSWER, AND IT IS THE CHEAPEST POSSIBLE AGREEMENT
--------------------------------------------------------------------
`claude_names: []` means the lane returned a structured read with no legible item names. That is an
answer, so it goes in the `both` bucket. But two empty lists agreeing proves nothing about either
eye, so `shapes.equal_both_empty` is reported separately and the headline agreement figure can be
read with it subtracted. The same care is why `one_sided` is not folded into `disagree`: a silent
lane is not a dissenting lane.

USAGE
-----
    python3 tv/g5_shadow_reducer.py                 # his live store, one-shot report
    python3 tv/g5_shadow_reducer.py --json          # same, machine-readable
    python3 tv/g5_shadow_reducer.py <path.jsonl>    # any store (fixtures)

    from g5_shadow_reducer import reduce_rows, divergence_row

⚠ THE LIVE STORE IS GITIGNORED AND MACHINE-LOCAL (tv/g5_shadow.jsonl, .gitignore:39). No gate may
read it — `reduce_rows` performs no file I/O at all so a test can only ever hand it fixtures, and
`divergence_row` reports state "unread" rather than failing when the store is absent, which is the
normal case on CI and on every machine but his.
"""
from __future__ import annotations

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# The writer is tv/g5_grok_eyes.py::_SHADOW_LOG. The two are pinned together by
# test_a_shadow_log_nobody_read_is_not_agreement.py rather than by an import, because importing
# g5_grok_eyes touches his per-machine state and budget files. [[the-unjoined-end]]
DEFAULT_LOG = os.path.join(HERE, "g5_shadow.jsonl")
DEFAULT_STATE = os.path.join(HERE, "g5_grok_eyes.state")

LANES = ("claude", "grok")

# Keys that would let a reader tell "the lane saw nothing" from "the lane failed and a sentinel was
# logged". If NONE of them is present the report says so out loud instead of quietly guessing.
_DISAMBIGUATING_KEYS = ("claude_conf", "grok_conf", "claude_mode", "grok_mode",
                        "claude_error", "grok_error", "claude_ok", "grok_ok")


# ── figures ───────────────────────────────────────────────────────────────────────────────────
def figure(n, d, first_ts=None, last_ts=None):
    """A number that cannot be published without its denominator and its window.

    pct is None when d is 0. A rate over nothing is unknown, never zero — the whole point of
    [[zero-needs-a-denominator]]. Callers format with fmt_figure(), which refuses to print a bare
    percent.
    """
    n = int(n)
    d = int(d)
    return {"n": n, "d": d,
            "pct": (round(100.0 * n / d, 1) if d else None),
            "first_ts": first_ts, "last_ts": last_ts}


def fmt_figure(f, unit="rows"):
    if not isinstance(f, dict):
        return "(no figure)"
    win = ("%s -> %s" % (f.get("first_ts"), f.get("last_ts"))) if f.get("first_ts") else "no window"
    if f.get("d"):
        return "%d/%d %s = %.1f%%  [%s]" % (f["n"], f["d"], unit, f["pct"], win)
    return "%d/%d %s = unknown (no denominator)  [%s]" % (f.get("n", 0), f.get("d", 0), unit, win)


# ── answeredness ──────────────────────────────────────────────────────────────────────────────
def answered_names(v):
    """A lane answered the NAMES question iff it produced a list. None = it did not answer."""
    return isinstance(v, list)


def answered_scene(v):
    """A lane answered the SCENE question iff it produced a non-empty string."""
    return isinstance(v, str) and v.strip() != ""


def names_key(v):
    """Order- and case-insensitive comparison key. Blank entries are not names."""
    return tuple(sorted(str(x).strip().lower() for x in (v or []) if str(x).strip()))


def scene_key(v):
    return str(v or "").strip().lower()


def _window(rows):
    ts = sorted(str(r.get("ts") or "") for r in rows if r.get("ts"))
    return (ts[0], ts[-1]) if ts else (None, None)


# ── the reducer ───────────────────────────────────────────────────────────────────────────────
def _bucket(rows, answered, key):
    """Partition rows into both / one_sided_claude / one_sided_grok / neither. EXACTLY."""
    both, one_c, one_g, neither = [], [], [], []
    for r in rows:
        c = answered(r.get("claude_" + key))
        g = answered(r.get("grok_" + key))
        if c and g:
            both.append(r)
        elif c:
            one_c.append(r)
        elif g:
            one_g.append(r)
        else:
            neither.append(r)
    return both, one_c, one_g, neither


def _names_field(rows):
    both, one_c, one_g, neither = _bucket(rows, answered_names, "names")
    bf, bl = _window(both)

    agree, disagree = [], []
    shapes = {"equal_both_empty": 0, "equal_nonempty": 0,
              "claude_empty_grok_saw": 0, "grok_empty_claude_saw": 0,
              "overlap_partial": 0, "disjoint_both_nonempty": 0}
    claude_only, grok_only = {}, {}
    for r in both:
        a, b = names_key(r.get("claude_names")), names_key(r.get("grok_names"))
        if a == b:
            agree.append(r)
            shapes["equal_both_empty" if not a else "equal_nonempty"] += 1
            continue
        disagree.append(r)
        sa, sb = set(a), set(b)
        if not sa:
            shapes["claude_empty_grok_saw"] += 1
        elif not sb:
            shapes["grok_empty_claude_saw"] += 1
        elif sa & sb:
            shapes["overlap_partial"] += 1
        else:
            shapes["disjoint_both_nonempty"] += 1
        # BOTH directions, always. Neither list is "the errors" — they are the two testimonies.
        for nm in sorted(sa - sb):
            claude_only[nm] = claude_only.get(nm, 0) + 1
        for nm in sorted(sb - sa):
            grok_only[nm] = grok_only.get(nm, 0) + 1

    d = len(both)

    def _top(counts):
        return [{"name": k, "rows": v, "share": figure(v, d, bf, bl)}
                for k, v in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))]

    return {
        "field": "names",
        "rows_total": len(rows),
        "both": d,
        "one_sided_claude": len(one_c),
        "one_sided_grok": len(one_g),
        "neither": len(neither),
        "agree": figure(len(agree), d, bf, bl),
        "disagree": figure(len(disagree), d, bf, bl),
        "shapes": shapes,
        # The headline with the free agreement removed: two empty lists matching is not two eyes
        # agreeing about anything on his screen.
        "agree_excluding_both_empty": figure(shapes["equal_nonempty"],
                                             d - shapes["equal_both_empty"], bf, bl),
        "top_divergences": {"claude_only": _top(claude_only), "grok_only": _top(grok_only)},
        "window": {"first_ts": bf, "last_ts": bl},
    }


def _scene_field(rows):
    both, one_c, one_g, neither = _bucket(rows, answered_scene, "scene")
    bf, bl = _window(both)

    agree = 0
    pairs = {}
    for r in both:
        a, b = scene_key(r.get("claude_scene")), scene_key(r.get("grok_scene"))
        if a == b:
            agree += 1
        else:
            pairs[(a, b)] = pairs.get((a, b), 0) + 1

    d = len(both)
    top = [{"claude_scene": k[0], "grok_scene": k[1], "rows": v, "share": figure(v, d, bf, bl)}
           for k, v in sorted(pairs.items(), key=lambda kv: (-kv[1], kv[0]))]
    return {
        "field": "scene",
        "rows_total": len(rows),
        "both": d,
        "one_sided_claude": len(one_c),
        "one_sided_grok": len(one_g),
        "neither": len(neither),
        "agree": figure(agree, d, bf, bl),
        "disagree": figure(d - agree, d, bf, bl),
        "top_divergences": top,
        "window": {"first_ts": bf, "last_ts": bl},
    }


def reduce_rows(rows, source=None):
    """Reduce already-loaded shadow rows to a report. NO FILE I/O — fixtures only, by construction.

    The four buckets partition the input exactly; the invariant is asserted here so a future edit
    that loses or double-counts a row is caught at the source rather than in a percentage.
    """
    rows = [r for r in (rows or []) if isinstance(r, dict)]
    fields = {"names": _names_field(rows), "scene": _scene_field(rows)}
    for f in fields.values():
        total = f["both"] + f["one_sided_claude"] + f["one_sided_grok"] + f["neither"]
        if total != len(rows):
            raise AssertionError("bucket partition lost rows on %r: %d != %d"
                                 % (f["field"], total, len(rows)))
        if f["agree"]["n"] + f["disagree"]["n"] != f["both"]:
            raise AssertionError("agree+disagree != both on %r" % f["field"])

    first_ts, last_ts = _window(rows)
    reach = {}
    for lane in LANES:
        reach[lane + "_names"] = figure(
            sum(1 for r in rows if answered_names(r.get(lane + "_names"))), len(rows),
            first_ts, last_ts)
        reach[lane + "_scene"] = figure(
            sum(1 for r in rows if answered_scene(r.get(lane + "_scene"))), len(rows),
            first_ts, last_ts)

    caveats = []
    present = set()
    for r in rows:
        present.update(r.keys())
    if rows and not (present & set(_DISAMBIGUATING_KEYS)):
        caveats.append(
            # ASCII ONLY. This string is PRINTED, and his console is cp1255: an em-dash here
            # raises UnicodeEncodeError while the report is reporting. Caught by this module's own
            # gate on its first run. [[console_safe]]
            "the record carries no per-lane confidence, mode or error, so a lane's [] cannot be "
            "told apart from a lane whose read failed and logged the EMPTY sentinel - every "
            "'agree, both empty' row below is therefore of unknown worth")
    if not rows:
        caveats.append("no rows: nothing here is evidence of agreement OR of disagreement")

    return {
        "source": source,
        "rows_total": len(rows),
        "window": {"first_ts": first_ts, "last_ts": last_ts},
        "fields": fields,
        "reach": reach,
        "caveats": caveats,
    }


# ── loading (the only file I/O in the module) ─────────────────────────────────────────────────
def load_rows(path=None):
    """Read a shadow store. Returns (rows, stats).

    A missing file is `exists: False` with zero rows — never an exception and never an empty store
    silently reported as a quiet one. Unparsable lines are COUNTED, because a store that is half
    corrupt must not publish a percentage as if it were whole.
    """
    path = path or DEFAULT_LOG
    stats = {"path": path, "exists": False, "lines": 0, "unparsable": 0}
    rows = []
    if not os.path.isfile(path):
        return rows, stats
    stats["exists"] = True
    with io.open(path, encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            ln = ln.strip()
            if not ln:
                continue
            stats["lines"] += 1
            try:
                obj = json.loads(ln)
            except Exception:
                stats["unparsable"] += 1
                continue
            if isinstance(obj, dict):
                rows.append(obj)
            else:
                stats["unparsable"] += 1
    return rows, stats


def read_mode(path=None):
    """The lane's declared mode, or 'unknown'. An unreadable state file is never 'off'."""
    path = path or DEFAULT_STATE
    try:
        with io.open(path, encoding="utf-8") as fh:
            st = json.load(fh)
        if not isinstance(st, dict):
            return "unknown"
        if not st.get("on"):
            return "off"
        return str(st.get("mode") or "unknown")
    except Exception:
        return "unknown"


# ── the doctor-callable row ───────────────────────────────────────────────────────────────────
def divergence_row(log_path=None, state_path=None):
    """One row a console doctor can render. It REPORTS; it does not judge either lane.

    States are its own, so it can never cry wolf on correct behaviour [[rule 8]]:
      unread      — no store on this machine. The store is gitignored, so this is the NORMAL state
                    on CI and on every machine but his. Not a fault.
      no-evidence — a store exists but no row has both lanes answering. Silence is not agreement.
      measured    — there is a figure, and it is published with its denominator and its window.
    """
    rows, stats = load_rows(log_path)
    mode = read_mode(state_path)
    if not stats["exists"]:
        return {"id": "g5-shadow-divergence", "state": "unread", "mode": mode,
                "label": "G5 two-eye divergence",
                "detail": "no shadow store at %s (gitignored, per-machine)" % stats["path"],
                "report": None, "store": stats}

    rep = reduce_rows(rows, source=stats["path"])
    n = rep["fields"]["names"]
    if n["both"] == 0:
        return {"id": "g5-shadow-divergence", "state": "no-evidence", "mode": mode,
                "label": "G5 two-eye divergence",
                "detail": ("%d rows, 0 with both lanes answering (%d claude-only, %d grok-only, "
                           "%d silent) — no agreement has been measured"
                           % (rep["rows_total"], n["one_sided_claude"], n["one_sided_grok"],
                              n["neither"])),
                "report": rep, "store": stats}
    return {"id": "g5-shadow-divergence", "state": "measured", "mode": mode,
            "label": "G5 two-eye divergence",
            "detail": ("names disagree %s; scene disagree %s; lane mode=%s"
                       % (fmt_figure(n["disagree"]),
                          fmt_figure(rep["fields"]["scene"]["disagree"]), mode)),
            "report": rep, "store": stats}


# ── the one-shot report ───────────────────────────────────────────────────────────────────────
def format_report(rep, mode=None, store=None, top=10):
    L = []
    w = rep["window"]
    L.append("G5 TWO-EYE SHADOW LOG - READ SIDE")
    L.append("source        : %s" % (rep.get("source") or "(in-memory rows)"))
    if store:
        L.append("store         : %d lines, %d unparsable" % (store["lines"], store["unparsable"]))
    L.append("rows          : %d      window: %s -> %s" % (rep["rows_total"], w["first_ts"], w["last_ts"]))
    if mode:
        L.append("lane mode     : %s   (a promotion rests on the figures below)" % mode)
    L.append("")
    L.append("REACH - how often each lane answered at all, of all rows in the window")
    for k in sorted(rep["reach"]):
        L.append("  %-16s %s" % (k, fmt_figure(rep["reach"][k])))

    for name in ("names", "scene"):
        f = rep["fields"][name]
        L.append("")
        L.append("%s" % name.upper())
        L.append("  both answered   : %d rows   [%s -> %s]"
                 % (f["both"], f["window"]["first_ts"], f["window"]["last_ts"]))
        L.append("  one-sided claude: %d rows   (claude spoke, grok silent - NOT a disagreement)"
                 % f["one_sided_claude"])
        L.append("  one-sided grok  : %d rows   (grok spoke, claude silent - NOT a disagreement)"
                 % f["one_sided_grok"])
        L.append("  neither answered: %d rows   (not evidence)" % f["neither"])
        L.append("  agree           : %s" % fmt_figure(f["agree"]))
        L.append("  disagree        : %s" % fmt_figure(f["disagree"]))
        if name == "names":
            sh = f["shapes"]
            L.append("  shapes          : equal-both-empty %d | equal-nonempty %d | "
                     "claude-empty-grok-saw %d | grok-empty-claude-saw %d | overlap %d | disjoint %d"
                     % (sh["equal_both_empty"], sh["equal_nonempty"], sh["claude_empty_grok_saw"],
                        sh["grok_empty_claude_saw"], sh["overlap_partial"],
                        sh["disjoint_both_nonempty"]))
            L.append("  agree, minus the free 'both empty' agreement:")
            L.append("                    %s" % fmt_figure(f["agree_excluding_both_empty"]))
            for lane in ("claude_only", "grok_only"):
                L.append("  top %-12s (names this lane reported and the other did not):" % lane)
                rowsx = f["top_divergences"][lane][:top]
                if not rowsx:
                    L.append("      (none)")
                for e in rowsx:
                    L.append("      %-34s %s" % (e["name"][:34], fmt_figure(e["share"])))
        else:
            L.append("  top scene divergences (claude -> grok), both published, neither preferred:")
            if not f["top_divergences"]:
                L.append("      (none)")
            for e in f["top_divergences"][:top]:
                L.append("      %-12s vs %-12s %s"
                         % (e["claude_scene"], e["grok_scene"], fmt_figure(e["share"])))

    if rep["caveats"]:
        L.append("")
        L.append("WHAT THIS RECORD CANNOT SAY")
        for c in rep["caveats"]:
            L.append("  - %s" % c)
    L.append("")
    L.append("This report resolves nothing. Both lanes are published with their reach; a "
             "disagreement rate is a finding about the INSTRUMENTS first.")
    return "\n".join(L)


def main(argv=None):
    try:
        from console_safe import enable as _enable
        _enable()
    except Exception:
        pass
    argv = list(argv if argv is not None else sys.argv[1:])
    as_json = "--json" in argv
    argv = [a for a in argv if not a.startswith("--")]
    path = argv[0] if argv else DEFAULT_LOG
    rows, stats = load_rows(path)
    if not stats["exists"]:
        print("no shadow store at %s (gitignored, per-machine) - nothing to read" % path)
        return 0
    rep = reduce_rows(rows, source=path)
    if as_json:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
    else:
        print(format_report(rep, mode=read_mode(), store=stats))
    return 0


if __name__ == "__main__":
    sys.path.insert(0, HERE)
    raise SystemExit(main())
