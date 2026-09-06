#!/usr/bin/env python3
"""A7 — every reel store has ONE declared owner, and everyone else is a declared reader.

His ask: *"all reels need to be processed the same way all unified logic"* — no reel gets a special
path, a bypass, or a second implementation, and any lane that differs is *"declared, in code, as a
deliberate exception with a reason"*.

⚠⚠ WHAT THIS DOES **NOT** DO, SAID FIRST BECAUSE IT IS THE THING A READER WOULD ASSUME. It does not
prove single-writer. I tried to measure that two ways before writing this and BOTH RETURNED ZERO
WRITERS for all four stores:

    a filename-adjacency grep      0 — the store name is never beside the write verb
    an AST walk resolving constants 0 — paths are bound in helpers (`TOMBSTONE_PATH = _tombstone_path()`)
                                        and threaded through arguments, which by-name resolution
                                        cannot follow

Two zeros in a row measured MY INSTRUMENTS, not the code, and a third detector would have been the
same mistake with more effort. So this takes the technique the codebase already uses and makes it
checkable instead: `reel_index.py` says "THE ONLY WRITER" in its docstring, `reel_repair.py` says
"exactly one writer of an index in the repo" — real declarations, in prose, that nothing verified.

WHAT IT DOES CHECK, and it is a ratchet rather than a proof:

  · every store names an OWNER, and that owner's source actually mentions the store — a
    declaration naming a module that has never heard of the file is worse than none
  · every OTHER module that mentions the store is listed as a declared reader WITH A REASON
  · a module that starts touching a store and is not declared FAILS, so a second implementation
    has to be argued in rather than appearing

That is evidence about COUPLING, not about writes. [[unknown-stays-unknown]] [[copy-drift]] §1

    python3 tv/store_owners.py
    python3 tv/store_owners.py --json
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

#: store -> who owns it, what it holds, and every module allowed to mention it.
#: ⚠ A reader is listed WITH ITS REASON. "It appears in the file" is not a reason; the point of the
#: list is that adding to it makes someone say out loud why another module needs this store.
STORES = {
    "retro_triage.json": {
        "owner": "retro_triage",
        "holds": "per-reel structural verdict: frames, panels, kinds",
        "readers": {
            "lane_liveness":  "NOT a toucher — its DOCSTRING cites this store as an example of a\n                              lane that leaves a dated row, which is the argument for why a\n                              heartbeat was NOT built as a second copy of that fact. Prose,\n                              never a read. Declared so the mention is accounted for",
            "verdict_provenance": "reads ONE row to ask whether it can name what produced it.\n                              41 stores swept, 21 SILENT. It writes nothing, back-fills\n                              nothing and never repairs — naming the gap is the product",
            "run_gates":      "NOT a toucher — a gate DESCRIPTION names this file while\n                              explaining what the gate is for. Prose in a `why` string",

            "write_census":      "NOT a writer of THIS file — it calls retro_triage.remember() with a "
                                 "SCRATCH root and watches which module the write is attributed to. It is "
                                 "the A7 measurement-by-observation, and the only one of the five stores "
                                 "that can be exercised at all. Declared so the mention is accounted for "
                                 "rather than reading as a second writer",
            "control_app":   "serves it to the console surfaces",
            "printer_reach": "the printer-zone acceptance test reads panels to find the A4 case",
            "declared_vs_content": "A15 — asks whether a reel's route is derived from its CONTENT "
                                   "or guessed from a declared stamp, so it needs what the "
                                   "structural pass actually found",
            "one_funnel":    "A15 clause 2 — counts how many reels this store has a DATED row for. "
                             "It quotes retro_triage.STORE rather than naming the file (REG-534)",
            "write_witness": "NOT a reader — it patches open/io.open/os.replace process-wide to "
                             "ATTRIBUTE writes, so it names this path only to report who wrote it",
            "reel_router":   "A7·ROUTE — the survey's verdict IS a station on the river, so the "
                             "router reads `panels` (via worth_reading, through printer.stream) "
                             "and `ts` to say WHEN a reel was surveyed. ⚠ It reads through "
                             "retro_triage's own load(), never the file, and writes nothing",
        },
    },
    "reel_tombstones.json": {
        "owner": "reel_retention",
        "holds": "reels that were pruned, and when — the record that a reel existed",
        "readers": {
            "tv_diablo":     "NOT a toucher — a v2639 comment explains that the recorder's\n                              emergency reaper is deliberately NOT a second writer of this\n                              store; reel_retention._tombstone stays the one writer, and the\n                              recorder records to its own reel_reaps.jsonl instead. Prose",
            "run_gates":     "NOT a toucher — a gate DESCRIPTION names this file while saying\n                              the reaper is not a second writer of it. Prose in a `why` string",

            "lane_liveness":  "NOT a toucher — its DOCSTRING cites this store as an example of a\n                              lane that leaves a dated row, which is the argument for why a\n                              heartbeat was NOT built as a second copy of that fact. Prose,\n                              never a read. Declared so the mention is accounted for",

            "write_census":      "NOT a writer and never can be — it names this store to record that only "
                                 "an actual DELETION writes a tombstone, and the prune stays OFF by his "
                                 "standing ruling, so its exercise is declared None WITH that reason. "
                                 "Naming what cannot be measured is the whole point of the census",
            "printer":           "READS it, once per snapshot, for the seventh station. v2692 gave "
                                 "the printer a `tombstone` station so the river ends where a reel "
                                 "actually ends -- 'if it is gone, what closed it out? (and this "
                                 "one is still here)'. It resolves the path through "
                                 "reel_retention._tombstone_path() rather than joining its own, so "
                                 "reel_retention stays the one authority on WHERE the store lives "
                                 "even though the printer is now a second READER of it. A failure "
                                 "to load leaves `tombstones` None, never {} -- nobody-looked and "
                                 "measured-empty are different answers here",
            "control_app":       "renders the tombstones on the shelf",
            "second_eye_ledger": "NOT a coupling — its docstring cites this file as the example of "
                                 "an untracked store living beside the reels. Declared so the "
                                 "mention is accounted for rather than looking like a second writer",
            "dead_field":        "reads it to ask whether a field is recorded on every row and "
                                 "filled on none — it found `startedTs` dead across 410 rows. It "
                                 "asks the OWNER for the path (reel_retention._tombstone_path) "
                                 "rather than resolving one itself, which is REG-540",
            "write_witness":     "NOT a reader — it patches open/io.open/os.replace process-wide "
                                 "to ATTRIBUTE writes, so it names this path only to report who "
                                 "wrote it. It is an instrument pointed at the store, never a "
                                 "second writer of it",
        },
    },
    "vault_accum.json": {
        "owner": "vault_retro",
        "holds": "what the vault sweep accumulated per reel",
        "readers": {
            "tv_diablo":     "v2639 — the disk-floor reel reaper READS the witness sessions so it\n                              can refuse to delete a reel the vault still cites as evidence.\n                              Read only, through a cached mtime check, and it writes nothing here.\n                              Its first victim would otherwise have been the reel behind\n                              'Chaotic Grand Charm'",

            "write_census":      "NOT a writer — it names this store to record that the vault lane writes "
                                 "it during a PAID sweep, and a sweep spends money and must not be started "
                                 "to satisfy a census. Exercise declared None, with that reason",
            "console_doctor":  "checks the vault stores are readable",
            "console_healer":  "repairs it when it will not parse",
            "control_app":     "serves the vault surfaces",
            "write_witness":   "NOT a reader — it patches open/io.open/os.replace process-wide to "
                               "ATTRIBUTE writes, so it names this path only to report who wrote it",
            "frame_authority": "the deletion authority reads it to protect witness frames",
            "reel_retention":  "eligibility consults what the vault took",
            "vault_doctor":    "audits the vault lane",
        },
    },
    "vault_swept.json": {
        "owner": "frame_authority",
        "holds": "the seal store — which sessions the vault sweep has sealed, and what it extracted",
        "readers": {
            "lane_liveness":  "NOT a toucher — its DOCSTRING cites this store as an example of a\n                              lane that leaves a dated row, which is the argument for why a\n                              heartbeat was NOT built as a second copy of that fact. Prose,\n                              never a read. Declared so the mention is accounted for",
            "verdict_provenance": "reads ONE row to ask whether it can name what produced it.\n                              41 stores swept, 21 SILENT. It writes nothing, back-fills\n                              nothing and never repairs — naming the gap is the product",

            "write_census":      "NOT a writer — same as vault_accum: the vault lane writes this as a paid "
                                 "sweep completes, so the exercise is declared None rather than run. "
                                 "UNEXERCISED and NO-WRITERS are different facts",
            "console_doctor":  "checks the vault stores are readable",
            "console_healer":  "repairs it when it will not parse",
            "control_app":     "serves the seal state to the console",
            "lane_health":     "reports whether the vault lane is moving",
            "reel_retention":  "asks whether both lanes are finished with a reel",
            "run_gates":       "names it in the list of stores a gate must not clobber",
            "vault_doctor":    "audits the vault lane",
            "vault_retro":     "writes what it swept, through the owner",
            "one_funnel":      "A15 clause 2 — counts how many reels this store has a DATED row "
                               "for, which is one of only two rungs on the six-rung ladder that "
                               "leaves a waypoint at all. It quotes frame_authority.SEAL_STORE "
                               "rather than naming the file, which is REG-534",
            "write_witness":   "NOT a reader — it patches open/io.open/os.replace process-wide to "
                               "ATTRIBUTE writes, so it names this path only to report who wrote it",
        },
    },
}


def _modules():
    """-> {module_name: source}. Test files and conftest are not part of the product graph."""
    out = {}
    for fn in sorted(os.listdir(HERE)):
        if not fn.endswith(".py") or fn.startswith("test_") or fn == "conftest.py":
            continue
        # ⚠⚠ THE REGISTRY MUST NOT COUNT ITSELF, AND IT CAUGHT ITSELF ON ITS FIRST RUN. This file
        # names every store — that IS the declaration — so it appeared as an undeclared toucher of
        # all four. Excluding it is only honest while it never actually OPENS one, which is not a
        # promise here: test_store_owners asserts this module contains no read or write of a store
        # path. An instrument that counts itself is a defect this console has produced before
        # (the deriver that counted itself as a watcher).
        if fn == "store_owners.py":
            continue
        # ⚠⚠ THE RAW SOURCE, COMMENTS AND ALL — AND I TRIED STRIPPING THEM AND MADE IT WORSE.
        # `audit()` asks `store in src`, so ANY mention of a store's filename reads as coupling.
        # On 2026-09-05 a comment I added to `run_gates.py`, naming the healer backups its
        # live-state net had been missing, made this report one undeclared toucher — and the only
        # occurrence in that file was that comment.
        #
        # The obvious fix is [[source-reading-guard]] §3.5's: grade code, not prose. I applied it,
        # and it BROKE THREE THINGS. Modules reach these stores through helpers rather than
        # literals, so the filename appears in their comments only — strip those and three honest
        # declarations turn into "stale allowances". ONE false positive became THREE.
        # ⚠ And the strip's own comment contained `open("<a store name>")` as an example, which
        # tripped the OTHER guard here — the one asserting this registry never opens what it
        # declares. The same defect, one level up, inside the fix for it.
        #
        # So the scan stays raw and the RULE is on the prose instead: **do not write a store's
        # literal filename in a comment in this tree.** Name it by role — "the healer backups",
        # "the vault accumulator" — which is more readable anyway. That is v1853's ruling applied
        # unchanged: the honest fix was to move MY comment out of someone else's window, not to
        # widen their window to accommodate me.
        try:
            out[fn[:-3]] = io.open(os.path.join(HERE, fn), encoding="utf-8").read()
        except Exception:
            pass
    return out


def audit():
    """-> {"ok", "rows", "why"}. Undeclared couplings are the finding."""
    mods = _modules()
    if not mods:
        return {"ok": False, "rows": [],
                "why": "no module could be read at all — UNKNOWN, not a clean graph"}
    rows = []
    for store, spec in sorted(STORES.items()):
        owner = spec["owner"]
        declared = set(spec["readers"]) | {owner}
        touching = {m for m, src in mods.items() if store in src}
        undeclared = sorted(touching - declared)
        # ⚠ A DECLARED READER THAT NO LONGER TOUCHES THE STORE IS ALSO A FINDING — the list stops
        # describing the code, and a stale allowance is how the next undeclared module slips in
        # under a name nobody re-checked.
        stale = sorted(declared - touching)
        rows.append({
            "store": store, "owner": owner, "holds": spec["holds"],
            "ownerMentionsIt": owner in touching,
            "declared": len(declared), "touching": len(touching),
            "undeclared": undeclared, "stale": stale,
        })
    bad = [r for r in rows if r["undeclared"] or r["stale"] or not r["ownerMentionsIt"]]
    return {
        "ok": not bad, "rows": rows,
        "why": ("%d store(s) declared, every module that mentions them accounted for. ⚠ This is "
                "COUPLING, not proof of a single writer — two static attempts to measure writers "
                "returned zero and were measuring the instrument." % len(rows)) if not bad else
               ("%d store(s) disagree with their declaration" % len(bad)),
    }


def main(argv):
    r = audit()
    if "--json" in argv:
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return 0
    print("\nSTORE OWNERS — one owner per reel store, everyone else declared\n")
    for row in r["rows"]:
        flag = "  " if not (row["undeclared"] or row["stale"]) else "⚠ "
        print("%s%-22s owner %-16s %d declared / %d touching"
              % (flag, row["store"], row["owner"], row["declared"], row["touching"]))
        if not row["ownerMentionsIt"]:
            print("     ⚠ the declared owner never mentions this store")
        for u in row["undeclared"]:
            print("     ⚠ UNDECLARED: %s touches this store and nothing says why" % u)
        for s in row["stale"]:
            print("     ⚠ STALE: %s is declared but no longer touches it" % s)
    print("\n  %s" % r["why"])
    return 0 if r["ok"] else 0        # reports; never fails a build


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    raise SystemExit(main(sys.argv[1:]))
