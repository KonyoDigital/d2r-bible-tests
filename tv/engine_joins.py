#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WHICH ENGINES ARE CONNECTED TO THE PRINTER, AND WHICH ARE STILL TALKING TO NOBODY.

Konyo, 2026-09-04: *"okay thats why the engines need connecting.. i want a unified logic and
communicating between them.. these partly built things arent worth alot if you dont connect them
together to work as a unit"*.

⚠⚠ WHY THIS EXISTS, AND WHY IT IS A CENSUS RATHER THAN A FIX. Four unjoined engines were found in
one afternoon, each by accident, each after the printer had already shipped a version without it:

    reel_segments   classified reels since v2343 · four consumers · NOT the printer   -> v2571
    extract_gap     the journal held 472 names the seals did not carry                -> v2572
    retro_triage    owns the 80/20 question, and joining it SPARED 10 reels            -> v2573

Finding these one at a time is the defect. A module that answers a question about a reel and is
never asked is worth nothing, and nothing was measuring how many of those there are.

★ JOINEDNESS IS DERIVED, NEVER DECLARED. The `joined` column is computed by walking printer.py's
own AST for what it imports — so a module that stops being consulted goes RED here without anyone
remembering to update a list. A hand-kept flag would rot into exactly the false green this file
exists to catch. [[the-unjoined-end]] [[source-reading-guard]]

⚠ WHAT THIS CANNOT TELL YOU, and a cold review named it: it proves a FIELD ARRIVED, not that
this engine put it there. If two modules could write the same key, a JOINED here means "the answer
is on the row", not "this module is why". Fixing that properly needs per-field provenance the rows
do not carry, so it is stated rather than papered over.

★ AND AN ENGINE MAY LEGITIMATELY NOT BELONG. `WHY_NOT` records the ones deliberately outside the
printer, WITH the reason, so "unjoined" never silently means "forgotten".

    python3 tv/engine_joins.py
    python3 tv/engine_joins.py --json
"""
import ast
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

UNIFIER = os.path.join(HERE, "printer.py")

#: a module importing more than this many repo modules is a HUB, not a reasoning path. Derived,
#: not named: control_app pulls 65 and would otherwise make every module in the tree look joined.
HUB_FANOUT = 15

#: module -> what it can tell you ABOUT A REEL. Only modules that answer a per-reel question
#: belong here; a module that reports on the shelf as a whole is a different kind of thing.
ENGINES = {
    # module -> (what it can tell you about a reel, the OUTPUT FIELD that proves it arrived).
    # A station owner needs no field: owning a station IS its answer arriving on every row.
    "one_start_point":     ("which door this reel entered by", None),
    "reel_river":          ("how far down the ladder it has come, and who decided", None),
    "reel_templates":      ("what the reel IS, and the extraction zone that follows", None),
    "per_reel_routes":     ("what chose its route — its content, or policy", None),
    "extract_gap":         ("whether it can be extracted, and if not whether that is "
                            "recoverable", None),
    "printer_reach":       ("whether the extraction contract admits its seal", "shelfReach"),
    "retro_triage":        ("whether a paid reader should see it — the 80/20 question",
                            "worthReading"),
    "reel_segments":       ("the activities on its timeline", "activities"),
    # ⚠ THE ONLY REAL WIRING GAP, and its scope is narrower than it looks. That a tooltip WAS
    # read is already on the row — extract_gap carries `names`, and 151 of 1,065 deep rows yielded
    # one. What tooltip_find alone can add is WHERE in the frame it sat, which needs an OCR pass
    # per frame. So this is not "the console knows nothing about tooltips"; it is "the position is
    # not carried", and the position is what slot identity would need.
    "tooltip_find":        ("WHERE in the frame the tooltip sat (that one WAS read is already "
                            "carried, by extract_gap's `names`)", "tooltip"),
    "slot_identity":       ("which cell an item sat in — the slot a name cannot fake", "slot"),
    "frame_authority":     ("whether its seal covers extraction", "sealed"),
    "declared_vs_content": ("whether its routing came from content or a stamp", "declared"),
    "main_character":      ("whose character the reel belongs to", "character"),
    "write_witness":       ("what testimony exists for what it yielded", "witness"),
}

#: ⚠⚠ v2580 — "UNJOINED" WAS ONE WORD FOR TWO DIFFERENT PROBLEMS, and only one of them is a
#: wiring job. Measured on his store 2026-09-04, asking what data each engine could even be fed:
#:
#:     slot_identity        0 of 1,065 deep rows carry a cell or slot. `names_loc` looks like it
#:                          might, and does not — it maps a NAME to a LANE ({"Wraithstep":
#:                          "stash"}), never to a grid position.
#:     main_character       0 of 1,065 rows carry a character. REG-340 already ruled this one: the
#:                          game prints the name on the character panel, which he does not film,
#:                          so it is a CAPTURE change and not a code change.
#:     declared_vs_content  its OWN state is UNTESTABLE — "only 0 declaring reel(s) carry surveyed
#:                          content (need 3)". There is no answer to carry.
#:     write_witness        exposes a Witness class and `watching`, not a per-reel reading.
#:
#: Telling him to wire those would be telling him to wire a pipe to a dry tap. A gap whose fix is
#: CAPTURE must not sit in the same column as a gap whose fix is an import. [[unknown-stays-unknown]]
NO_DATA = {
    "slot_identity": "0 of 1,065 deep rows carry a cell or slot. `names_loc` maps a NAME to a "
                     "LANE, never to a grid position — so there is no slot answer to carry yet. "
                     "The fix is capture, not wiring",
    "main_character": "0 of 1,065 deep rows carry a character. REG-340: the game prints it on the "
                      "character panel, which he does not film. Capture, not wiring",
    "declared_vs_content": "its own state is UNTESTABLE — 0 declaring reels carry surveyed "
                           "content where it needs 3. There is no answer to carry",
    "write_witness": "it exposes a Witness class and `watching`, not a per-reel reading. Nothing "
                     "of the shape the printer could quote exists yet",
}

#: deliberately outside the printer, with the reason. An entry here is a DECISION, not a gap.
WHY_NOT = {
    "reel_segments": "joined INDIRECTLY and correctly — reel_templates quotes it, and the printer "
                     "quotes reel_templates. A second direct import would be two paths to one "
                     "answer, which is the drift this whole file is against",
    "frame_authority": "joined INDIRECTLY through extract_gap, which asks it for the seals. The "
                       "printer must not hold its own opinion about a seal",
}


def _imports_of(path):
    """Every module printer.py imports, at any depth in its body. -> set

    ⚠ AST, NOT A TEXT SEARCH. Every one of these names also appears in the printer's prose — it
    NAMES its owners in the docstring and in STATION_OWNER — so a substring match would report a
    module as joined because the file mentions it. That is the exact shape of the guard that fired
    on its own docstring at v2570. [[source-reading-guard]]
    """
    try:
        with io.open(path, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
    except Exception:
        return None
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                out.add(a.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.level == 0:
                out.add(node.module.split(".")[0])
    return out


def _surfaced(rep=None):
    """Which engines actually SURFACE in the printer's output. -> (dict, why)

    ⚠⚠ THIS REPLACED TWO WRONGER INSTRUMENTS, AND THE ITERATION IS THE POINT.

      cut 1  direct imports only  -> called retro_triage UNJOINED, an hour after I joined it
                                    through reel_templates. Too strict: a real join read as a gap.
      cut 2  transitive imports   -> called tooltip_find JOINED via
                                    console_doctor <- control_app <- extract_gap. control_app
                                    imports 40 repo modules; routing through a hub makes
                                    everything look connected. Too generous.
      cut 3  hub-excluded         -> STILL called tooltip_find JOINED, via
                                    vault_retro <- reel_retention <- reel_river. A real import
                                    chain, and still not evidence that a tooltip answer reaches
                                    a reel.

    An import is a dependency, not a join. The only honest question is whether the ANSWER arrives,
    so this runs the printer and looks at what its rows actually carry. A station IS an answer
    arriving; anything else has to name the field it contributes and be found in the output.
    [[feedback-suspect-the-instrument]] [[feedback-verify-not-proxy]]
    """
    # ⚠ `rep` MAY BE HANDED IN. The console already runs printer.stream() once per heart open
    # (printer_state), and a second run here would double the cost of a panel he opens constantly
    # — and could disagree with the rows he is looking at if the shelf moved between the two
    # calls. One reading, two readers. [[copy-drift]] §1
    try:
        import printer as P
        if rep is None:
            rep = P.stream()
    except Exception as e:
        return None, "the printer would not run (%s)" % str(e)[:90]
    rows = rep.get("rows") or []
    if not rows:
        return None, "the printer returned no reel, so nothing could be observed arriving"
    owners = {v[0] for v in getattr(P, "STATION_OWNER", {}).values()}
    # ⚠⚠ v2579 — TWO DEFECTS HERE, BOTH FOUND BY A COLD CROSS-FAMILY LOOK AT THE v2574 BYTES,
    # both measured on his real shelf before being believed.
    #
    # 1. IT SAMPLED FIVE ROWS AND REPORTED A VERDICT OVER FORTY. An engine that contributes only
    #    to later reels was invisible. "A sample is not a verdict" is a rule this repo already
    #    has; I broke it in the file whose whole job is catching that shape.
    #
    # 2. IT TESTED NON-EMPTINESS, NOT PRESENCE, so a legitimately EMPTY answer read as an answer
    #    that never arrived. Measured: `activities` is `[]` on 14 of his 40 reels — an honest
    #    measurement meaning "this reel has no classified activity" — and `[]` was filtered out.
    #    A five-row sample landing on those would have flipped a correct JOINED to UNJOINED. It
    #    did not today, which is luck, not design. [[unknown-stays-unknown]]
    #
    # A key that is PRESENT is an answer that arrived; what the answer says is a different
    # question and not this file's.
    fields = set()
    for row in rows:
        for st in (row.get("stations") or {}).values():
            fields.update((st or {}).keys())
    return {"owners": owners, "fields": fields, "reels": len(rows)}, ""


def census(rep=None):
    """-> dict. Which engines' answers actually arrive at a reel.

    `rep` is an already-computed printer.stream() reading, so a caller that has one does not pay
    for a second and cannot disagree with itself about the same shelf.
    """
    obs, why = _surfaced(rep)
    if obs is None:
        return {"ok": False, "state": "UNKNOWN", "rows": [], "counts": {},
                "why": "%s — UNKNOWN, never 'nothing is joined'" % why}
    rows, counts = [], {}
    for mod in sorted(ENGINES):
        spec = ENGINES[mod]
        answers, field = (spec if isinstance(spec, tuple) else (spec, None))
        if mod in obs["owners"]:
            state, why = "JOINED", "it OWNS a station — its answer is on every reel row"
        elif field and field in obs["fields"]:
            state, why = "JOINED", ("its %r reaches the row, carried by the station that quotes it"
                                    % field)
        elif mod in WHY_NOT:
            state, why = "BY DESIGN", WHY_NOT[mod]
        elif mod in NO_DATA:
            state, why = "NO DATA", NO_DATA[mod]
        else:
            state = "UNJOINED"
            why = ("nothing the printer prints carries its answer. It can tell you '%s' and that "
                   "reaches no reel. An import is not a join." % answers)
        rows.append({"engine": mod, "answers": answers, "state": state, "why": why})
        counts[state] = counts.get(state, 0) + 1
    # ⚠ NO DATA is NOT counted as unjoined. Rolling them together is what made this panel say
    # "5 answer nobody asks" when four of them have no answer to give — a number that reads as
    # five afternoons of wiring and is actually one import and a capture change.
    unjoined = counts.get("UNJOINED", 0)
    return {
        "ok": True, "rows": rows, "counts": counts, "unjoined": unjoined,
        "observedOn": obs["reels"],
        "state": ("CONNECTED" if not unjoined else "PARTIAL"),
        # ⚠ THE SUMMARY NAMES THE DRY TAPS TOO. A cold review pointed out that CONNECTED/PARTIAL
        # keys only on UNJOINED, so a run with four engines that have NO DATA still reads
        # CONNECTED. That is intended — a dry tap is not a wiring gap — but a reader seeing only
        # "CONNECTED" would take it as everything being wired, which is not what it says.
        "why": ("%d engine(s) answer a question about a reel, checked against what the printer "
                "actually printed for %d of them. %s%s%s"
                % (len(rows), obs["reels"],
                   " · ".join("%s %d" % (k, v) for k, v in sorted(counts.items())),
                   ("" if not unjoined else
                    "  ⚠ %d answer nobody asks." % unjoined),
                   ("" if not counts.get("NO DATA") else
                    "  ⚠ %d more have NO DATA to give — a capture gap, not a wiring one, and "
                    "CONNECTED does not mean those are answered."
                    % counts.get("NO DATA")))),
    }


def main(argv):
    r = census()
    if "--json" in argv:
        print(json.dumps(r, indent=2, sort_keys=True, default=str))
        return 0
    print("\nENGINE JOINS — who the printer actually asks\n")
    if not r["ok"]:
        print("  %s\n" % r["why"])
        return 1
    for row in r["rows"]:
        print("  %-12s %-20s %s" % (row["state"], row["engine"], row["answers"]))
        if row["state"] != "JOINED":
            print("               %s" % row["why"][:150])
    print("\n  %s\n" % r["why"])
    return 0


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
