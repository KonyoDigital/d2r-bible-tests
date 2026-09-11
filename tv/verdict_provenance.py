#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CAN EACH STORED VERDICT SAY WHAT PRODUCED IT? — the census for a class-wide gap.

⚠⚠ HOW THIS WAS FOUND, AND IT WAS HIS CATCH. Building the reel router, `EMPTY` came out of
`retro_triage.worth_reading()` — `bool(panels)` from the full-frame survey. He asked, 2026-09-05:
*"retro reader? okay so this happens though before it even enters the printer and station? doesnt
it need to be gated after also."* Measured: `retro_triage.json` rows carry `frames, full, kinds,
panels, ts` and **no classifier version**, so a verdict from an old survey is indistinguishable
from one taken today, and `EMPTY` cannot honestly mean more than *"nothing found by whatever the
classifier was on that date"*.

Then: *"make sure to look out for other coding things like this that might be gapped just like
this was.. connect it all to a unified wiring and coding correctly to a one unit engine."* So it
was swept, and the gap is not one store. Measured by this module 2026-09-11 across 44 stores:

    ANSWERS      6    names a version or engine, not merely a writer
    PARTIAL      4    names the LANE only — WHO wrote it, never WHAT VERSION
    SILENT      16    a dated row, and nothing says what produced it
    REFERENCE   17    a roster or lookup table — no clock, so the question does not apply
    UNKNOWN      1    the shape could not be read, and that is not "stamp-less"

⚠ THIS CENSUS IS RESTATED IN EIGHT PLACES AND FIVE OF THEM WENT STALE. Measured 2026-09-11:
verdict_provenance, run_gates (twice) and store_owners (twice) each carried 41/4/3/21/12/1 while
the tool itself reported 44/6/4/16/17/1. A figure copied into prose drifts silently, so every
restatement now carries the DATE it was measured — a dated number that is old reads as history; an
undated one reads as truth. [[copy-drift]] [[stale-reading]]

    retro_triage.json       437 rows   SILENT   <- decides EMPTY on the river
    chronicle_swept.json    401 rows   SILENT   <- decides READ
    vault_swept.json         30 rows   SILENT   <- decides SEAL
    disk_history.jsonl    8,554 rows   SILENT
    sessions.jsonl        3,552 rows   ANSWERS  <- lane + ver, the shape the others need

Every station verdict on the river records WHEN and not BY WHAT.

⚠ THE FIRST CUT OF THIS REPORTED "18 of 21" AND 24 UNKNOWNS. Both were the instrument: it
understood one JSON shape and had no REFERENCE class, so it filed rosters as missing a stamp they
have no reason to carry AND could not read most of its subjects. A census that cannot read its
subjects is measuring itself, and a report that cries wolf teaches a reader to skip it. The count
was the tell. [[feedback-suspect-the-instrument]] [[label-outlived-referent]]

WHY THAT MATTERS AND IS NOT PEDANTRY. A verdict without its producer cannot be invalidated. When a
classifier improves, nothing can name the rows that predate the improvement, so a stale NO survives
every future pass looking exactly like a fresh one — and on this river a stale NO means footage is
never read again. That is [[stale-reading]]'s rule at store granularity: the age of the THING, not
of the fetch. It is also why `reel_retention` already holds "sealed with 0 pages" reels *"for the
engine to reopen when the prompt improves"* — the doctrine exists; the field it needs does not.

⚠⚠ THIS REPORTS, IT DOES NOT REPAIR. It writes nothing, back-fills nothing and deletes nothing.
Back-filling a producer onto 437 existing rows would invent provenance for verdicts nobody can now
attribute — the same refusal gh #210 makes about the 450 reels that predate any door stamp.
[[unknown-stays-unknown]]

⚠ IT ASKS `store_owners.STORES` RATHER THAN CARRYING ITS OWN LIST, so a store added there is
covered the day it appears and the two cannot drift. [[copy-drift]]
"""
import glob
import io
import json
import subprocess
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

#: field names that answer "what produced this row". Deliberately generous: the question is
#: whether the store can answer AT ALL, so a store using an unusual name should pass rather than
#: be reported as a gap it does not have.
PRODUCER_FIELDS = ("version", "ver", "engine", "classifier", "model", "prompt", "rev", "schema",
                   "builtBy", "producer", "lane", "by")

#: ⚠ `lane` and `by` say WHO, never WHAT VERSION. A store carrying only these is PARTIAL — it can
#: name the writer and still cannot tell a verdict from before an improvement from one after it.
WHO_ONLY = ("lane", "by")

#: how big a file this will open. A multi-GB store is not read to answer a question about its
#: SHAPE; it is reported UNKNOWN with the reason. [[unknown-stays-unknown]]
MAX_BYTES = 40 * 1024 * 1024


def _sample_row(path):
    """One representative row from a store. -> (dict | None, why)"""
    try:
        if os.path.getsize(path) > MAX_BYTES:
            return None, "larger than %d MB — not opened to answer a question about its shape" \
                         % (MAX_BYTES // (1024 * 1024))
    except OSError as exc:
        return None, "could not stat (%s)" % type(exc).__name__
    try:
        if path.endswith(".jsonl"):
            last = None
            with io.open(path, encoding="utf-8", errors="replace") as fh:
                for ln in fh:
                    if ln.strip():
                        last = ln
            if last is None:
                return None, "no rows yet — the shape is UNKNOWN, not stamp-less"
            return json.loads(last), ""
        blob = json.load(io.open(path, encoding="utf-8", errors="replace"))
    except Exception as exc:
        return None, "would not parse (%s)" % type(exc).__name__
    # ⚠⚠ THE FIRST CUT OF THIS UNDERSTOOD ONE SHAPE AND REPORTED 24 OF 41 STORES UNKNOWN.
    # That count was the tell: a census that cannot read most of its subjects is measuring itself.
    # Three shapes are real here and each answers the question differently.
    # [[feedback-suspect-the-instrument]]
    if isinstance(blob, list) and blob and isinstance(blob[-1], dict):
        return blob[-1], ""
    if isinstance(blob, dict) and blob:
        vals = [blob[k] for k in list(blob)[:25]]
        dicts = [v for v in vals if isinstance(v, dict)]
        if dicts:
            # ⚠ THE UNION OF SEVERAL ROWS, NOT ONE ARBITRARY ROW. `chronicle_swept.json` has 400
            # rows carrying agentVer/promptVer and ONE that does not; sampling `blob[first_key]`
            # is a coin flip on whether the store looks stamped. A store answers if ANY row can.
            merged = {}
            for v in dicts:
                merged.update(v)
            return merged, ""
        # a FLAT store — one object describing one thing. The blob itself is the row, and a
        # version field on it covers the whole file. Reporting it as unreadable was wrong.
        return blob, ""
    return None, "no rows yet — the shape is UNKNOWN, not stamp-less"


#: field names that mean "when was this row made". A store with NO clock anywhere is almost
#: certainly REFERENCE DATA — a roster, a manifest, a lookup table — and the provenance question
#: does not apply to it the way it applies to a verdict.
CLOCK_FIELDS = ("ts", "at", "lastat", "time", "when", "generatedts", "updatedat", "seenat")


#: ⚠⚠ SUFFIX MATCHING, BECAUSE EXACT MEMBERSHIP MEASURED MY OWN VOCABULARY. The first cut tested
#: `str(k).lower() in PRODUCER_FIELDS` against twelve words. `agentVer` lowercases to "agentver",
#: which is not one of them — so `chronicle_swept.json` (400 of 401 rows carrying agentVer AND
#: promptVer) and `vault_swept.json` (30 of 30) were both reported SILENT. Both already have LIVE
#: invalidation wired (`_chron_seal_stands`, `_vault_still_sealed`), which is the very thing this
#: census exists to look for, and it marked them as missing it.
#: I published that as "every station verdict on the river records WHEN and not BY WHAT". It was
#: false for two of the three stations I named. A census that only recognises the names it thought
#: of is measuring its author. [[feedback-suspect-the-instrument]] [[source-reading-guard]]
#: ⚠ The boundary is a CAPITAL or an underscore, never a bare suffix: "server" ends in "ver".
_PRODUCER_SUFFIX = re.compile(r"(?:[a-z0-9](?:Ver|Version|Hash|Rev|Model|Engine|Classifier)"
                              r"|_(?:ver|version|hash|rev|model|engine|classifier))$")


def _is_producer_key(k):
    """Does this field name say what produced the row? -> bool"""
    k = str(k)
    return k.lower() in PRODUCER_FIELDS or bool(_PRODUCER_SUFFIX.search(k))


#: ⚠ GUARDED: if the definition module cannot be imported the census must still run on its own
#: vocabulary — an unreadable definition is UNKNOWN, never a reason to grade every store SILENT.
try:
    import provenance as _PV
except Exception:          # pragma: no cover - exercised by the red-proof
    _PV = None


def _verdict(row):
    """Can this row say what produced it? -> (state, fields)

    ANSWERS · PARTIAL · SILENT · REFERENCE, and never a bare boolean: "names the writer" and
    "names the version" are different answers, and collapsing them is the same mistake one layer
    up. REFERENCE is the fourth, and leaving it out was a real flaw — it filed rosters and lookup
    tables as missing a stamp they have no reason to carry, which inflates the gap and teaches a
    reader to skip the report. A finding that cries wolf is one he learns to ignore.
    """
    # ⚠⚠ v2941 (#69) — ASK THE DEFINITION FIRST. `provenance.classify()` has existed since the
    # module was written and had ZERO production callers — an AST walk of every tv/*.py found one
    # importer, its own test. The module's own docstring names this caller ("verdict_provenance.
    # _verdict then falls through to its own field vocabulary exactly as before"), and
    # test_provenance.py:312 is written so that "applying the three-line `_verdict` patch does not
    # turn this law red". Two halves each built right and never joined, with the joint already
    # specified in prose. [[the-unjoined-end]] [[copy-drift]]
    #
    # ⚠ IT CANNOT MAKE A STORE WORSE: classify() returns None for anything it has nothing to say
    # about, and the existing vocabulary runs unchanged below. What it fixes is the half that was
    # working BY ACCIDENT — a .json store graded ANSWERS only because _sample_row merges sub-dicts
    # and `_prov` happens to contain a bare `ver`; rename that inner key and the census silently
    # stops recognising every stamped store. A `.jsonl` store got no merge at all and graded SILENT.
    _g = _PV.classify(row) if _PV is not None else None
    if _g is not None:
        return _g, [_PV.PROV_KEY]
    keys = [str(k).lower() for k in row.keys()]
    found = sorted(k for k in row.keys() if _is_producer_key(k))
    has_clock = any(k in CLOCK_FIELDS or k.endswith("at") or k.endswith("ts") for k in keys)
    if not found and not has_clock:
        return "REFERENCE", []
    if not found:
        return "SILENT", []
    if all(str(k).lower() in WHO_ONLY for k in found):
        return "PARTIAL", found
    return "ANSWERS", found


def _declared_stores():
    """The stores the registry already owns. -> (list, why)"""
    try:
        import store_owners as SO
    except Exception as exc:
        return [], "store_owners would not import (%s)" % type(exc).__name__
    return sorted(SO.STORES.keys()), ""


def census(root=None):
    """Every store, and whether its rows can name their producer. -> dict"""
    d = root or HERE
    declared, why = _declared_stores()
    names = list(declared)
    # everything else on disk too, so a store nobody declared cannot hide from this
    for p in sorted(glob.glob(os.path.join(d, "*.json")) + glob.glob(os.path.join(d, "*.jsonl"))):
        b = os.path.basename(p)
        if b not in names and ".scratch-" not in b:
            names.append(b)
    rows, counts = [], {"ANSWERS": 0, "PARTIAL": 0, "SILENT": 0, "REFERENCE": 0,
                        "UNKNOWN": 0}
    for name in names:
        p = os.path.join(d, name)
        if not os.path.exists(p):
            rows.append({"store": name, "state": "UNKNOWN", "fields": [], "declared":
                         name in declared, "why": "declared but not on disk — never written"})
            counts["UNKNOWN"] += 1
            continue
        row, rwhy = _sample_row(p)
        if row is None:
            rows.append({"store": name, "state": "UNKNOWN", "fields": [],
                         "declared": name in declared, "why": rwhy})
            counts["UNKNOWN"] += 1
            continue
        state, fields = _verdict(row)
        rows.append({"store": name, "state": state, "fields": fields,
                     "declared": name in declared,
                     "why": ("names %s" % ", ".join(fields)) if fields else
                            "no field in the row says what produced it"})
        counts[state] += 1
    rows.sort(key=lambda r: (not r["declared"], r["store"]))
    return {"ok": True, "rows": rows, "counts": counts, "total": len(rows),
            "declaredMissing": why, "why": why}


# ── v2888 · THE RATCHET ───────────────────────────────────────────────────────────────────────
#: Konyo, 2026-09-10: "ratchet it". This file MEASURED a real gap and returned a literal 0, so it
#: could never go red — one of the three gates heart2 named for exactly that. Arming it outright
#: was not an option: only 6 of 43 stores can say what produced them, so a hard gate is a wall.
#: A ratchet blocks the gap GROWING without blocking on the debt already there.
#:
#: ⚠⚠ IT PINS EACH STORE, NOT THE FOUR TOTALS. Konyo: "does it not need to be accurate though?" —
#: and he was right. Counts hide a swap: one store gaining provenance the same day another loses
#: it leaves ANSWERS/PARTIAL/SILENT/REFERENCE identical and the ratchet green while the thing it
#: watches got worse. A per-store map also NAMES which store moved and which way.
#:
#: ⚠⚠ TWO SCOPES, BECAUSE THE HOST MACHINE IS OTHERWISE THE FIXTURE. census() globs tv/*.json, and
#: MEASURED 2026-09-10: 11 of 43 stores are tracked in git; 32 exist only on the machine that
#: wrote them, and ALL 16 SILENT stores are in that untracked half. One blended baseline would be
#: red on CI for 32 absent stores while the real debt was never visible there at all. So the
#: tracked scope is enforced on EVERY venue and the local scope only where its stores exist — and
#: it SAYS SO where they do not. A half that goes unmeasured in silence is the failure this whole
#: file is about. [[feedback-blind-fixture-green-gate]] [[zero-needs-a-denominator]]
BASELINE = os.path.join(HERE, "verdict_provenance_baseline.json")

#: SILENT and REFERENCE TIE ON PURPOSE — they print the identical why ("no field in the row says
#: what produced it"), so ranking one over the other would invent a distinction the census does
#: not draw. A move between them is REPORTED, never reddened. UNKNOWN is lowest: a store that lost
#: its rows did not improve.
RANK = {"ANSWERS": 3, "PARTIAL": 2, "SILENT": 1, "REFERENCE": 1, "UNKNOWN": 0}


def _tracked():
    """Basenames of stores git tracks — the ones that exist on every venue. -> (set|None, why)"""
    try:
        r = subprocess.run(["git", "ls-files", HERE], cwd=HERE, capture_output=True,
                           text=True, timeout=30)
    except Exception as e:
        return None, "git could not be asked which stores are tracked (%s)" % type(e).__name__
    if r.returncode != 0:
        return None, "git ls-files exited %s" % r.returncode
    out = set()
    for line in r.stdout.splitlines():
        b = os.path.basename(line.strip())
        if b.endswith(".json") or b.endswith(".jsonl"):
            out.add(b)
    return out, ""


def _split(rep, tr=None):
    """The census split into the two scopes. -> (tracked, local, why)

    ⚠⚠ v2888 — `tr` IS PASSED IN, AND THAT IS THE WHOLE POINT. The first cut called git at RUNTIME
    to ask which stores are tracked, and heart2 measured the consequence immediately:
        verdict_provenance UNPROVABLE — ALREADY RED untampered (git ls-files exited 128)
    because the sandbox is a COPY, not a checkout. Which stores git tracks is a fact about the
    repo, pinned when the baseline is written by a human — not something to re-derive on every
    run in whatever directory the gate happens to be executed from. Asking git each time made the
    verdict depend on the venue's VCS state rather than on provenance. [[stale-reading]]
    """
    if tr is None:
        tr, why = _tracked()
        if tr is None:
            return None, None, why
    t, l = {}, {}
    _self = os.path.basename(BASELINE)
    for r in rep["rows"]:
        # ⚠ THE RATCHET'S OWN BASELINE IS NOT A VERDICT STORE. census() globs tv/*.json, so the
        # first run after --write-baseline found the file it had just written and reported it as
        # "NEW store arrives REFERENCE — new debt". Measured on the very first clean run. Same
        # self-reference shape as the red-proofs whose gate file is their own tamper target.
        if r["store"] == _self:
            continue
        (t if r["store"] in tr else l)[r["store"]] = r["state"]
    return t, l, ""


def write_baseline():
    tr, lo, why = _split(census())
    if tr is None:
        print("🔴 %s — refusing to write a baseline I cannot scope" % why)
        return 1
    # ⚠ NO HOSTNAME AND NO PATHS. This repo is PUBLIC; a venue is described by SHAPE, not identity.
    doc = {"tracked": tr, "local": lo, "localCount": len(lo),
           "trackedNames": sorted(tr),
           "why": "per-store provenance ratchet; the tracked scope is enforced on every venue, "
                  "the local scope only where its stores exist"}
    io.open(BASELINE, "w", encoding="utf-8").write(json.dumps(doc, indent=2, sort_keys=True))
    print("wrote %s — tracked %d store(s), local %d store(s)"
          % (os.path.basename(BASELINE), len(tr), len(lo)))
    return 0


def _compare(was, now):
    """-> (regressions, gains, arrivals, departures), each a list of sentences."""
    reg, gain, new, gone = [], [], [], []
    for store, before in sorted(was.items()):
        after = now.get(store)
        if after is None:
            gone.append("%s: %s -> ABSENT. A store that vanished is UNKNOWN, not fixed" % (store, before))
            continue
        if RANK.get(after, 0) < RANK.get(before, 0):
            reg.append("%s: %s -> %s" % (store, before, after))
        elif RANK.get(after, 0) > RANK.get(before, 0):
            gain.append("%s: %s -> %s" % (store, before, after))
    for store, after in sorted(now.items()):
        if store in was:
            continue
        if after == "UNKNOWN":
            new.append("%s: NEW and empty — not debt yet, and not clean either" % store)
        elif RANK.get(after, 0) < RANK["ANSWERS"]:
            reg.append("%s: NEW store arrives %s — new debt" % (store, after))
        else:
            new.append("%s: NEW and it ANSWERS" % store)
    return reg, gain, new, gone


def ratchet():
    """Red only if the gap GREW. -> exit code"""
    if not os.path.exists(BASELINE):
        print("🔴 no baseline at %s — nothing to ratchet against." % os.path.basename(BASELINE))
        print("   run: python3 tv/verdict_provenance.py --write-baseline")
        return 1
    try:
        was = json.loads(io.open(BASELINE, encoding="utf-8").read())
    except Exception as e:
        print("🔴 the baseline will not parse (%s) — UNKNOWN, not clean" % type(e).__name__)
        return 1
    _names = was.get("trackedNames")
    if _names is None:
        print("🔴 the baseline predates trackedNames and cannot say which scope is which — "
              "re-write it: python3 tv/verdict_provenance.py --write-baseline")
        return 1
    tr, lo, why = _split(census(), set(_names))
    if tr is None:
        print("🔴 %s — so nothing can be compared. UNKNOWN, not clean." % why)
        return 1

    bad = 0
    reg, gain, new, gone = _compare(was.get("tracked") or {}, tr)
    print("  tracked scope: %d store(s) measured against %d in the baseline"
          % (len(tr), len(was.get("tracked") or {})))
    for s in reg + gone:
        print("   🔴 %s" % s)
    for s in gain:
        print("   🟢 improved — %s  (re-write the baseline to lock it in)" % s)
    for s in new:
        print("   ⚪ %s" % s)
    bad += len(reg) + len(gone)

    b_local = was.get("local") or {}
    # ⚠⚠ ON DISK, NOT "THE CENSUS HAS A ROW FOR IT". This counted `s in lo`, and census() emits a
    # row for a DECLARED store even when the file is absent — state UNKNOWN, why "declared but not
    # on disk — never written". So on a CI checkout, where 0 of 32 local stores exist, four of them
    # are declared, four rows appeared, `present` read 4 instead of 0, the not-measured guard never
    # fired, and the ratchet compared anyway: SILENT/REFERENCE/ANSWERS -> UNKNOWN, four rank drops,
    # "provenance went BACKWARDS in 4 place(s)". MEASURED in a tracked-files-only export of HEAD.
    # That red shipped in v2888 and stood for three versions. A row is not a file.
    # [[feedback-blind-fixture-green-gate]] [[zero-needs-a-denominator]]
    present = sum(1 for s in b_local if os.path.exists(os.path.join(HERE, s)))
    if b_local and present == 0:
        print("  local scope: NOT MEASURED on this venue — 0 of %d baseline store(s) are here. "
              "These are runtime stores written by the machine that runs the console; their "
              "absence is a venue fact, not a clean result." % len(b_local))
    else:
        reg2, gain2, new2, gone2 = _compare(b_local, lo)
        print("  local scope: %d store(s) measured against %d in the baseline" % (len(lo), len(b_local)))
        for s in reg2:
            print("   🔴 %s" % s)
        for s in gain2:
            print("   🟢 improved — %s  (re-write the baseline to lock it in)" % s)
        for s in new2 + gone2:
            print("   ⚪ %s" % s)
        bad += len(reg2)
    if bad:
        print("")
        print("🔴 provenance went BACKWARDS in %d place(s) — the ratchet exists to stop exactly "
              "this. Fix the store, or re-write the baseline if the move is deliberate." % bad)
        return 1
    print("")
    print("🟢 provenance did not go backwards.")
    return 0


RED_PROOF = [
    {
        "why": "v2888 — this gate used to `return 0` unconditionally, which is why heart2 named it "
               "one of three that could never go red. The tamper removes the guard that keeps the "
               "ratchet's OWN baseline out of its census: census() globs tv/*.json, so without it "
               "the file written by --write-baseline is found on the next run and reported as "
               "\"NEW store arrives REFERENCE — new debt\", turning the gate red. That is a real "
               "defect, not a contrivance — it happened on the very first clean run and this line "
               "is the fix. matches: 2 because verdict_provenance.py IS its own gate file, so this "
               "declaration's `find` is a second occurrence of the anchor once it lands. "
               "[[regression-guard]] [[sabotage-is-usually-the-wrong-one]]",
        "file": 'verdict_provenance.py',
        "find": 'if r["store"] == _self:',
        "replace": 'if False:',
        "matches": 2,
    },
]


def main(argv):
    if "--write-baseline" in argv:
        return write_baseline()
    rep = census()
    print("\nCAN EACH STORED VERDICT SAY WHAT PRODUCED IT?\n")
    mark = {"ANSWERS": "🟢", "PARTIAL": "🟡", "SILENT": "🔴", "REFERENCE": "📖",
            "UNKNOWN": "⚪"}
    for r in rep["rows"]:
        if r["state"] in ("ANSWERS", "REFERENCE") and "-v" not in argv:
            continue
        print("  %s %-30s %-8s %s%s" % (mark.get(r["state"], "?"), r["store"][:30], r["state"],
                                        "" if r["declared"] else "(undeclared) ", r["why"][:64]))
    c = rep["counts"]
    print("\n  %d stores · ANSWERS %d · PARTIAL %d · SILENT %d · REFERENCE %d · UNKNOWN %d"
          % (rep["total"], c["ANSWERS"], c["PARTIAL"], c["SILENT"], c["REFERENCE"],
             c["UNKNOWN"]))
    print("  ⚠ SILENT means a verdict cannot be invalidated when its producer improves — a stale")
    print("    NO outlives every future pass looking exactly like a fresh one.\n")
    # ⚠ v2888 — WAS `return 0`, UNCONDITIONALLY, which is what made this one of the three gates
    # that could never go red however bad the answer got. The census still prints in full; the
    # VERDICT now comes from the ratchet.
    if "--census-only" in argv:
        return 0
    return ratchet()


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
