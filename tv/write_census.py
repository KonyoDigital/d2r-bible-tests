#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WHO ACTUALLY WRITES EACH REEL STORE — the measurement A7 had never taken.

A7's remaining half, in its own words: *"IT IS AN INSTRUMENT, NOT A MEASUREMENT — a sweep has to
run while it is on, and the per-store answer is a measurement NOBODY HAS TAKEN."*

⚠⚠ WHY THIS WAS OPEN SO LONG, and it is the whole shape of the task. THREE separate attempts to
answer "who writes this store" returned ZERO for all four stores, and every zero measured the
instrument rather than the tree:

    a filename-adjacency grep          0 writers — paths are bound in helpers
    an AST walk resolving constants    0 writers — paths are threaded through arguments
    write_witness patching only open   0 writers — this codebase uses io.open, and the write
                                       that matters is <name>.tmp then os.replace

`store_owners` closed the coupling question by DECLARATION. This closes the writer question by
OBSERVATION: arm the witness, run something that really writes, and read back who did it.

★ IT NEVER TOUCHES HIS STORES. Every exercise runs against a scratch root. The writer's IDENTITY
does not change with the path, which is the only thing being asked here.

★ AND A STORE NOBODY EXERCISED IS **NOT EXERCISED**, NEVER "no writers". The tombstone is only
written by an actual deletion, and the prune stays OFF — so that row says so instead of reporting
a zero that would read like an answer. [[unknown-stays-unknown]]

    python3 tv/write_census.py
    python3 tv/write_census.py --json
"""
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)


def _exercise_retro_triage(root):
    """retro_triage.remember() — a real survey record, written to a scratch root."""
    import retro_triage as RT
    RT.remember(os.path.join(root, "reel_s_1_1"), hits=1, frames=3,
                kinds={"stash": 1}, root=root, panel_frames={"stash": 1})
    return True


#: store -> (what would write it, an exercise that really does, or None when it cannot be run here)
EXERCISES = {
    "retro_triage.json": ("retro_triage.remember() records a survey", _exercise_retro_triage),
    "reel_tombstones.json": (
        "only an actual DELETION writes a tombstone, and the prune stays OFF by his standing "
        "ruling — so this cannot be exercised without removing footage", None),
    "vault_accum.json": (
        "written by the vault lane during a paid sweep; a sweep spends money and must not be "
        "started to satisfy a census", None),
    "vault_swept.json": (
        "same — the vault lane writes it as a sweep completes", None),
    "chron_evidence.json": (
        "written when the chronicle lane banks evidence, which needs a real read", None),
}


def census():
    """-> dict. Per store: who was OBSERVED writing it, or why nobody could look."""
    try:
        import write_witness as WW
    except Exception as e:
        return {"ok": False, "state": "UNKNOWN", "rows": [],
                "why": "the write witness will not import (%s)" % str(e)[:80]}
    # ⚠⚠ THIS READ THE WRONG THING AND THE SUMMARY WENT GREEN ON IT. The first cut asked
    # `store_owners.report()`, which returns {} — there is no such function; the declarations live
    # in `STORES`. So `declared` was empty, every agreement check came back None rather than
    # False, no disagreement could be found, and the summary announced "every observed writer is
    # the store's declared owner" having compared NOTHING. A vacuous truth reported as a result,
    # in a module written to close a task that had already been defeated three times by
    # instruments measuring themselves. Caught before it shipped by asking what report() actually
    # returned. [[feedback-suspect-the-instrument]] [[unknown-stays-unknown]]
    declared, declared_why = {}, ""
    try:
        import store_owners as SO
        for store, spec in (getattr(SO, "STORES", {}) or {}).items():
            if isinstance(spec, dict) and spec.get("owner"):
                declared[str(store)] = str(spec["owner"])
        if not declared:
            declared_why = "store_owners declared no owners at all"
    except Exception as e:
        declared_why = "store_owners would not answer (%s)" % str(e)[:70]

    rows = []
    for store in sorted(EXERCISES):
        why, fn = EXERCISES[store]
        if fn is None:
            rows.append({"store": store, "state": "NOT EXERCISED", "observed": None,
                         "declared": declared.get(store), "why": why})
            continue
        d = tempfile.mkdtemp(prefix="wc_")
        try:
            with WW.watching() as W:
                fn(d)
            hits = [e for e in (W.events or []) if str(e.get("store")) == store]
            by = sorted({str(e.get("by")) for e in hits})
            modes = sorted({str(e.get("mode")) for e in hits})
            if not hits:
                rows.append({"store": store, "state": "WATCHED AND SAW NOTHING", "observed": [],
                             "declared": declared.get(store),
                             "why": ("%s ran with the witness armed and wrote nothing — which is "
                                     "evidence only because something that SHOULD have written "
                                     "did run" % why)})
            else:
                dec = declared.get(store)
                agrees = (dec in by) if dec else None
                rows.append({"store": store, "state": "MEASURED", "observed": by,
                             "modes": modes, "declared": dec, "agreesWithOwner": agrees,
                             "why": ("%d write(s) witnessed by %s via %s"
                                     % (len(hits), ", ".join(by), ", ".join(modes)))})
        except Exception as e:
            rows.append({"store": store, "state": "UNKNOWN", "observed": None,
                         "declared": declared.get(store),
                         "why": "the exercise raised %s: %s" % (type(e).__name__, str(e)[:70])})
        finally:
            shutil.rmtree(d, True)

    meas = [r for r in rows if r["state"] == "MEASURED"]
    disagree = [r for r in meas if r.get("agreesWithOwner") is False]
    # ⚠ AN UNCHECKED CLAIM IS NOT A PASSED ONE. If nothing was declared, or a measured store has
    # no declaration, the agreement sentence must not be printed as though it had been tested.
    unchecked = [r for r in meas if r.get("agreesWithOwner") is None]
    # ⚠⚠ v2592 — `ok` WAS TRUE HAVING MEASURED NOTHING, and this is a GATE. A cold review asked
    # for every state where ok is True while nothing was established, and the answer was: all of
    # them. NOT EXERCISED rows are skipped, WATCHED-AND-SAW-NOTHING rows are skipped, and an
    # unchecked comparison is skipped — so with every exercise removed the census reported ok=True
    # with measured=0 and the gate exited 0. Reproduced exactly that way before fixing it.
    #
    # A pass now REQUIRES at least one store measured AND compared against its declared owner.
    # retro_triage is exercisable today, so if this ever drops to zero something real has broken —
    # which is the only condition under which a gate should be green. [[unknown-stays-unknown]]
    confirmed = [r for r in meas if r.get("agreesWithOwner") is True]
    return {
        "ok": bool(confirmed) and not disagree, "rows": rows,
        "confirmed": len(confirmed),
        "measured": len(meas), "total": len(rows),
        "state": ("MEASURED" if not disagree else "DISAGREES"),
        "why": (("NOTHING WAS ESTABLISHED — no store was both measured and compared to a "
                 "declared owner, so this is UNPROVEN rather than clean. " if not confirmed else "")
                + "%d of %d store(s) had a writer OBSERVED at runtime; the rest are NOT EXERCISED "
                "with the reason, never reported as having no writers. %s"
                % (len(meas), len(rows),
                   (("Every observed writer is the store's declared owner."
                     if not unchecked else
                     "⚠ %d measured store(s) could not be compared to a declared owner (%s), so "
                     "no agreement was tested — that is UNCHECKED, not agreement."
                     % (len(unchecked), declared_why or "no declaration for that store"))
                    if not disagree else
                   "⚠ %d store(s) were written by someone other than their declared owner."
                   % len(disagree)))),
    }


def main(argv):
    r = census()
    if "--json" in argv:
        print(json.dumps(r, indent=2, sort_keys=True, default=str))
        return 0
    print("\nWHO WRITES EACH REEL STORE — observed at runtime, not inferred\n")
    for row in r["rows"]:
        print("  %-14s %-22s %s" % (row["state"], row["store"],
                                    ", ".join(row.get("observed") or []) or "—"))
        print("                 %s" % str(row.get("why"))[:112])
    print("\n  %s\n" % r["why"])
    return 0 if r.get("ok") else 1


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
