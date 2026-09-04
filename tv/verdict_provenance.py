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
was swept, and the gap is not one store. Measured by this module across 41 stores:

    ANSWERS      4    names a version or engine, not merely a writer
    PARTIAL      3    names the LANE only — WHO wrote it, never WHAT VERSION
    SILENT      21    a dated row, and nothing says what produced it
    REFERENCE   12    a roster or lookup table — no clock, so the question does not apply
    UNKNOWN      1    the shape could not be read, and that is not "stamp-less"

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


def _verdict(row):
    """Can this row say what produced it? -> (state, fields)

    ANSWERS · PARTIAL · SILENT · REFERENCE, and never a bare boolean: "names the writer" and
    "names the version" are different answers, and collapsing them is the same mistake one layer
    up. REFERENCE is the fourth, and leaving it out was a real flaw — it filed rosters and lookup
    tables as missing a stamp they have no reason to carry, which inflates the gap and teaches a
    reader to skip the report. A finding that cries wolf is one he learns to ignore.
    """
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


def main(argv):
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
    return 0


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
