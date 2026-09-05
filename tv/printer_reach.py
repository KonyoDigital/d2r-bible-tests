#!/usr/bin/env python3
"""A4·A7·A8·A9·A15 — the printer zone's acceptance test: what can the pipeline ACT on at all?

His ask, 2026-09-03: *"i want this related to the 3/4D printer it should be in the same zone. that
unified printer needs to be built, that processing system for the reels all need a unified logic
coming in and out"*. Before building that, one question decides how much of it is real work:
**how much of the corpus can the pipeline reach today, and how much is structurally out of reach?**

⚠⚠ THE ANSWER IS NOT "IT IS CLEAN", AND THE ROUTE TO GETTING IT WRONG IS SHORT. The contradiction
A4 was born from — reels claiming "examined, nothing to take" while a survey says they held panels
— returns ZERO on this tree. That zero is NOT a pipeline shown healthy. Measured 2026-09-03:

    30 seals in the store
    22 carry an `extracted` record — and it is EMPTY on every one of them
     8 predate the extraction contract entirely

⚠ THE LINE ABOVE USED TO READ "ALL 22 fail on the SAME single fact: `name`". That was FALSE and
this module manufactured it itself: the loop keyed its tally on `str(cwhy)[:70]`, and 70 characters
lands part-way through the FIRST missing fact's explanation, so every distinct refusal collapsed
into one bucket that happened to end inside the word `name`. Re-measured 2026-09-05 without the
cut: **name, location AND provenance are missing on all 30 seals.** The correction matters because
the two readings imply different work — one missing fact is a reader change; `location` missing is
a CAPTURE question (0 of 1,065 deep rows carry a cell), and that is his ruling to make, not mine.
    -> 0 seals satisfy EXTRACTION_CONTRACT, so no reel can become disposable,
       so the contradiction is STRUCTURALLY UNREACHABLE rather than absent.

A count of zero taken through a filter that rejects every input measures the filter.
[[unknown-stays-unknown]] — and I have made exactly this mistake twice this week, so it is the
first thing this module says out loud rather than a caveat at the bottom.

⚠ AND `name` IS NOT A BUG TO FIX HERE. `_CONTRACT_WHY` says it: *"the item's name, which only ever
appears in a hover tooltip"*. A reel of a plain stash GRID has no names in it — BUGS.md REG-340
recorded the same thing for characters, and the vault audit ruled "film cannot name grids" to be
DESIGN, not a defect. So a grid-only reel can never satisfy the contract, can never be judged
disposable, and is permanently outside what the printer may act on. That is the guard working.

WHAT THIS REPORTS, and the three answers are deliberately different words:

    CLEAN         the join was made, seals were readable, and no seal certifying full extraction
                  sits on a reel the survey says held panels
    CONTRADICTION at least one does — the A4 case, and the printer must not ship without handling it
    UNREACHABLE   nothing could be compared: no seal satisfies the contract, or nothing joined.
                  NOT a pass. It is this module saying it could not see.

    python3 tv/printer_reach.py            # the report
    python3 tv/printer_reach.py --json
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

TRIAGE = os.path.join(HERE, "retro_triage.json")

CLEAN = "CLEAN"
CONTRADICTION = "CONTRADICTION"
UNREACHABLE = "UNREACHABLE"

#: ⚠⚠ REG-543 — UNREACHABLE WAS DOING TWO JOBS AND THEY ARE OPPOSITE FACTS. It meant BOTH
#: *"I measured, and the contradiction is structurally impossible on this corpus"* — a real,
#: hard-won finding — AND *"I could not read the seal store, so nothing was established."* Only
#: the `why` told them apart, so any consumer branching on `state` could not, and a store that
#: failed to open would read as the measured result. Measured: stubbing `sealed_sessions` to
#: return unreadable produced `state=UNREACHABLE`, byte-identical to the live tree's verdict.
#: Nothing-was-established is its own state. [[unknown-stays-unknown]]
UNKNOWN = "UNKNOWN"


def _triage():
    """-> (rows, why). A store that will not parse is UNKNOWN, never an empty corpus."""
    try:
        with io.open(TRIAGE, encoding="utf-8") as fh:
            blob = json.load(fh)
    except Exception as e:
        return None, "retro_triage.json could not be read (%s)" % str(e)[:80]
    if not isinstance(blob, dict):
        return None, "retro_triage.json is %s, not a mapping of reels" % type(blob).__name__
    return {k: v for k, v in blob.items() if isinstance(v, dict)}, ""


def _session_of(reel_key):
    """`reel_s_123_45` -> `s_123_45`. The two stores are keyed differently and that is the join."""
    k = str(reel_key or "")
    return k[len("reel_"):] if k.startswith("reel_") else k


def report():
    """-> dict. Never claims CLEAN on evidence it could not gather."""
    tri, why = _triage()
    # ⚠ REG-546 — every return carries the same keys; these three dropped `blocked`, so a caller
    # reading it broke on exactly the paths that mean NOTHING WAS ESTABLISHED.
    if tri is None:
        return {"state": UNKNOWN, "why": why, "rows": [], "counts": {}, "blocked": {}, "missingByFact": {}}
    try:
        import frame_authority as FA
    except Exception as e:
        return {"state": UNKNOWN, "rows": [], "counts": {}, "blocked": {}, "missingByFact": {},
                "why": "frame_authority will not import (%s), so no seal can be read" % str(e)[:70]}
    seals, ok = FA.sealed_sessions()
    if not ok or not isinstance(seals, dict):
        return {"state": UNKNOWN, "rows": [], "counts": {}, "blocked": {}, "missingByFact": {},
                "why": "the seal store could not be read — that is UNKNOWN, not an unsealed corpus"}

    # how many seals could EVER let a reel become disposable, and why the rest cannot
    satisfied, blocked, missing_by_fact = [], {}, {}
    for key, row in seals.items():
        covers, cwhy = FA.seal_covers_extraction(row if isinstance(row, dict) else {})
        if covers:
            satisfied.append(key)
        else:
            # ⚠⚠ v2645 — `[:70]` MANUFACTURED A FALSE FINDING AND THIS FILE PUBLISHED IT.
            # The refusal names every missing fact in one sentence; cutting at 70 characters lands
            # part-way through the FIRST fact's explanation, so every row read as "fails on name".
            # This module's own docstring then stated "ALL 22 fail on the SAME single fact: name".
            # MEASURED 2026-09-05 untruncated: name, location AND provenance are missing on ALL 30
            # seals — the shelf fails on THREE facts, not one, and the difference decides whether
            # the fix is one reader change or a capture change. A window that cuts a sentence in
            # half does not shorten the finding, it invents a different one.
            # [[source-window-shortcut]] [[label-outlived-referent]]
            key_why = str(cwhy)
            blocked[key_why] = blocked.get(key_why, 0) + 1
            # per-FACT tally, so "which fact" is answerable without reading prose
            _ex = row.get("extracted") if isinstance(row, dict) else None
            _have = set(_ex) if isinstance(_ex, list) else set()
            for _f in FA.EXTRACTION_CONTRACT:
                if _f not in _have:
                    missing_by_fact[_f] = missing_by_fact.get(_f, 0) + 1

    joined, contradictions = 0, []
    for rk, t in tri.items():
        row = seals.get(_session_of(rk)) or seals.get(rk)
        if row is None:
            continue
        joined += 1
        covers, _w = FA.seal_covers_extraction(row if isinstance(row, dict) else {})
        panels = int(t.get("panels") or 0)
        if covers and panels > 0:
            contradictions.append({"reel": rk, "panels": panels,
                                   "frames": int(t.get("frames") or 0)})

    counts = {"reels": len(tri), "seals": len(seals), "joined": joined,
              "sealsSatisfyingContract": len(satisfied)}
    if contradictions:
        return {"state": CONTRADICTION, "rows": contradictions, "counts": counts,
                "blocked": blocked, "missingByFact": missing_by_fact,
                "why": ("%d reel(s) carry a seal certifying full extraction while the survey says "
                        "they still held panels. This is the case A4 was born from and the printer "
                        "may not ship without handling it." % len(contradictions))}
    # ⚠ THE ZERO HAS TO EARN THE WORD "CLEAN".
    if not satisfied:
        return {"state": UNREACHABLE, "rows": [], "counts": counts, "blocked": blocked, "missingByFact": missing_by_fact,
                "why": ("NOT ONE of the %d seals satisfies the extraction contract, so no reel can "
                        "be judged disposable and the contradiction cannot arise at all. Zero "
                        "contradictions here measures the CONTRACT REFUSING EVERY SEAL, not a "
                        "pipeline shown healthy. Blocking reasons: %s"
                        % (len(seals), "; ".join("%s (x%d)" % (w, n)
                                                 for w, n in sorted(blocked.items(),
                                                                    key=lambda kv: -kv[1])[:2])))}
    if not joined:
        return {"state": UNREACHABLE, "rows": [], "counts": counts, "blocked": blocked, "missingByFact": missing_by_fact,
                "why": ("no triage row joined a seal, so nothing was compared. The two stores are "
                        "keyed differently (`reel_<session>` against `<session>`) and a zero here "
                        "would be measuring the join, not the corpus.")}
    return {"state": CLEAN, "rows": [], "counts": counts, "blocked": blocked, "missingByFact": missing_by_fact,
            "why": ("%d reel(s) joined a seal and %d seal(s) certify full extraction; none of them "
                    "sits on a reel the survey says held panels." % (joined, len(satisfied)))}


def main(argv):
    r = report()
    if "--json" in argv:
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return 0
    c = r.get("counts") or {}
    print("\nPRINTER REACH — what the pipeline can act on at all\n")
    print("  reels in triage            %s" % c.get("reels", "?"))
    print("  seals in the store         %s" % c.get("seals", "?"))
    print("  triage rows joining a seal %s" % c.get("joined", "?"))
    print("  seals satisfying contract  %s" % c.get("sealsSatisfyingContract", "?"))
    for w, n in sorted((r.get("blocked") or {}).items(), key=lambda kv: -kv[1]):
        print("     blocked x%-3d %s" % (n, w))
    print("\n  %s" % r.get("state"))
    print("  %s" % r.get("why"))
    for row in (r.get("rows") or [])[:8]:
        print("     ⚠ %s panels=%s frames=%s" % (row["reel"], row["panels"], row["frames"]))
    return 0


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    raise SystemExit(main(sys.argv[1:]))
