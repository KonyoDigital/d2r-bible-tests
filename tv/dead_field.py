#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A FIELD THAT HAS NEVER ONCE CARRIED A VALUE — and the console should be the one that notices.

His instruction, 2026-09-04: *"connect it to the heart of the console that way we would have
caught it"*.

⚠⚠ WHAT WAS NOT CAUGHT. `reel_retention._tombstone` recorded each deleted reel's `startedTs` as
`ix.get("startedTs") or ix.get("ts") or None` — two keys **no reel index has ever carried** (0 of
40, measured). It wrote `None` **410 times out of 410**, on the one door with no undo, and nothing
anywhere said so. It was found by reading a line. That is the wrong detector: a line gets read once,
and this field had been dead for 410 deletions.

So the console asks the question instead, on every heart read. The rule is deliberately narrow:

    a field PRESENT on every row and CARRYING A VALUE on none of them is not a field, it is a
    typo with a comma after it.

⚠ AND THE FLOOR IS THE WHOLE DESIGN. Null in 2 rows is a young store; null in 410 is a defect.
Under `MIN_ROWS` the answer is UNKNOWN — not "clean" — because a zero over rows that could not
disagree measures the sample, which is the mistake A15 clause 1 was written to avoid.
[[unknown-stays-unknown]]

⚠ IT REPORTS AND REFUSES NOTHING. Nothing here fails a build or blocks a button. A field can be
legitimately null for a long time (`focus` on a reel with no declared focus), so this is EVIDENCE
for a reader, exactly as CF-13's reach rows are.

    python3 tv/dead_field.py
    python3 tv/dead_field.py --json
"""
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

#: Below this many rows, a column of nulls is a young store and the answer is UNKNOWN. 30 is the
#: floor because the defect that produced this file survived 410 rows — anything that would not
#: have caught THAT is not worth wiring, and anything much smaller reports noise on a fresh tree.
MIN_ROWS = 30

#: The stores this watches, and WHO RESOLVES THE PATH. Deliberately short: he ruled *"I DO NOT want
#: this to randomly just connect wires to it if theres no need"*, so a store earns a line here by
#: having a record somebody acts on, not by existing. `reel_tombstones` is here because it is the
#: permanent record of the ONE action with no undo.
#:
#: ⚠⚠ REG-540 — THE FIRST CUT HARDCODED "reel_tombstones.json" RELATIVE TO THIS DIRECTORY, and the
#: owner does NOT resolve it that way. `reel_retention._tombstone_path(hist)` picks a fixture root,
#: a hist dir, or HERE. Reproduced: passing a hist dir — the shape the deleter actually runs in —
#: sends its tombstones to `<hist>/reel_tombstones.json` while this read `tv/reel_tombstones.json`.
#: **The detector would have watched a file the deletions never reach**, reporting on stale rows
#: forever with nothing saying so. That is the third time in one session the same shape has been
#: caught (REG-534 filenames, REG-537 a frozen snapshot, this a path resolved two ways), so this
#: one asks the owner. [[copy-drift]] §1: name ONE source, everything else quotes it.
#:
#: ⚠ THE LIMIT, STATED. Asking `_tombstone_path()` with no argument gives the store THE CONSOLE
#: OWNS — the one its own deletions land in. It does not follow a per-call `hist` override, and it
#: is not meant to: that is a caller's scope, not the console's store.
WATCHED = (
    ("reel_tombstones", ("reel_retention", "_tombstone_path"), "reels"),
)


def _path_of(src):
    """Resolve a store's path by asking its owner. -> (abs path, why)

    ⚠ An owner that will not import, or that stopped exposing its resolver, returns None WITH A
    REASON — never a guessed path, because a guess would read a file that may not be the store and
    report ITS rows as the store's. [[unknown-stays-unknown]]
    """
    if isinstance(src, str):
        # a literal is still accepted, for a store with no owner — but only a RELATIVE one.
        # ⚠ REG-542, from the cold look at v2540: `os.path.join(HERE, "/etc/passwd")` returns
        # "/etc/passwd". An absolute literal escapes this tree silently and the reading would then
        # report SOME OTHER FILE'S rows as the store's, with nothing saying it had left.
        if os.path.isabs(src):
            return None, ("%r is an absolute path — this resolves stores relative to the tree, and "
                          "an absolute literal would read a file that is not the store" % src)
        return os.path.join(HERE, src), ""
    try:
        mod, fn = src
    except Exception:
        return None, "the store has no resolver and no filename"
    try:
        # ⚠ REG-542 — `__import__("pkg.sub")` RETURNS THE TOP-LEVEL PACKAGE, so the getattr below
        # looked for the resolver in the wrong module and reported "no longer exposes …()" — the
        # module blamed for dropping a function it never had. A wrong REASON is the defect here:
        # it sends a reader to fix the wrong file. `import_module` returns the module named.
        import importlib
        m = importlib.import_module(mod)
    except Exception as e:
        return None, "%s would not import, so its store cannot be located (%s)" % (mod, str(e)[:50])
    f = getattr(m, fn, None)
    if not callable(f):
        return None, "%s no longer exposes %s(), so its store cannot be located" % (mod, fn)
    try:
        p = f()
    except Exception as e:
        return None, "%s.%s() would not answer (%s)" % (mod, fn, str(e)[:50])
    if not p:
        return None, "%s.%s() named no path" % (mod, fn)
    return str(p), ""


def _rows_of(src, key):
    """-> (rows, why). A store that will not read is UNKNOWN, never an empty store."""
    p, why = _path_of(src)
    if not p:
        return None, why
    path = os.path.basename(p)
    if not os.path.isfile(p):
        return None, "%s is not on disk, so nothing was asked of it" % path
    try:
        blob = json.loads(io.open(p, encoding="utf-8").read())
    except Exception as e:
        return None, "%s would not read (%s)" % (path, str(e)[-70:])
    rows = blob.get(key) if isinstance(blob, dict) else blob
    if not isinstance(rows, list):
        return None, "%s holds no list at %r — it is %s" % (path, key, type(rows).__name__)
    return [r for r in rows if isinstance(r, dict)], ""


def _is_filled(v):
    """Did this cell record something? -> bool

    ⚠⚠ REG-544 — THE FIRST CUT ASKED `v is not None and v != "" and v != []`, AND THAT WAS FOUR
    LITERALS PRETENDING TO BE A RULE. Measured across 40-row stores: `""` and `[]` read as nothing
    recorded, while `{}` and `()` — the same idea — read as a VALUE. Which answer you got depended
    on which literal happened to be in the condition.

    The rule, stated once: a cell is filled unless it is None, or it is a CONTAINER holding
    nothing. `0`, `0.0` and `False` are measured VALUES and stay filled — a cold review claimed the
    opposite about them and was refuted by measurement (they count 40 of 40, because `0 != ""` is
    True); calling a measured zero dead is the exact collapse this module exists to prevent.
    """
    if v is None:
        return False
    if isinstance(v, (bool, int, float)):
        return True                      # a number is a value, including 0 / 0.0 / False
    try:
        return len(v) > 0                # str, list, dict, tuple, set — empty means nothing recorded
    except TypeError:
        return True                      # anything with no length is an object, and objects are values


def dead_fields(rows, min_rows=MIN_ROWS):
    """Which fields are present on every row and filled on none? -> dict

    A field is DEAD only when it appears on EVERY row (so it is meant to be there) and no row
    carries a value. A field that is merely sometimes-null is a field with sometimes nothing to
    say, which is a different fact and is not reported.
    """
    # ⚠ REG-544 — EVERY RETURN CARRIES THE SAME KEYS. The early returns used to omit `judged` and
    # `skipped` while the later ones carried them, so a consumer reading `r["judged"]` raised
    # KeyError on exactly the paths that mean "nothing was established" — the reading breaks in the
    # state it exists to report. A shape that changes with the verdict is not a shape.
    def _unknown(why, checked=0, skipped=0, judged=0):
        return {"state": "UNKNOWN", "dead": [], "checked": checked, "skipped": skipped,
                "judged": judged, "fields": [], "filled": {}, "why": why}

    if rows is None:
        return _unknown("the store could not be read, so no field was judged")
    # ⚠ A generator reached `len()` and raised TypeError — a detector must not crash on the shape
    # of its input. Materialise it, so an iterator is judged like a list.
    if not isinstance(rows, (list, tuple)):
        try:
            rows = list(rows)
        except Exception as e:
            return _unknown("the rows could not be read as a sequence (%s)" % str(e)[:70])
    n = len(rows)
    if n < min_rows:
        return _unknown(("%d row(s) is under the %d-row floor — a column of nulls here is a young "
                         "store, and a zero over rows that cannot disagree measures the sample"
                         % (n, min_rows)), checked=n, judged=n)
    # ⚠ A ROW THAT IS NOT A DICT CRASHED THIS. Found by the cold cross-family look at v2539:
    # `dead_fields([{...}, None, {...}])` raised AttributeError on `r.keys()`. `state()` filters
    # before calling, so the live path was safe — but this function is PUBLIC, the guard calls it
    # directly, and a detector that crashes on malformed data goes silent exactly when the data is
    # bad. Skipped and COUNTED, because dropping rows silently would shrink the denominator the
    # floor is measured against. [[unknown-stays-unknown]]
    on_every, filled, skipped = None, {}, 0
    for r in rows:
        if not isinstance(r, dict):
            skipped += 1
            continue
        keys = set(r.keys())
        on_every = keys if on_every is None else (on_every & keys)
        for k, v in r.items():
            if _is_filled(v):
                filled[k] = filled.get(k, 0) + 1
    # ⚠⚠ REG-541 — THE FLOOR MUST COUNT ROWS THAT COULD BE JUDGED, NOT ROWS THAT EXISTED, and the
    # first cut of the skip counted them the wrong way. Measured on the version that shipped:
    #
    #     40 rows, ALL of them non-objects  ->  state OK, why "every field present on all 40
    #                                           row(s) carries a value somewhere"
    #
    # A wholly unreadable store reported CLEAN, with a sentence that is flatly false, from the one
    # module whose entire job is refusing to call the unmeasured clean. `n` was the row COUNT and
    # the judging used `on_every`, which stays None when nothing was a dict — so `dead` came back
    # empty and empty read as OK. The denominator is now what was actually judged, the floor is
    # applied to THAT, and the skip is named in EVERY branch rather than only when something was
    # already wrong. [[unknown-stays-unknown]]
    judged = n - skipped
    _skip_note = ((" \u26a0 %d of %d row(s) were not objects and could not be judged."
                   % (skipped, n)) if skipped else "")
    if judged < min_rows:
        return _unknown(("only %d of %d row(s) could be judged, under the %d-row floor — a verdict "
                         "here would be about the rows that happened to parse, not about the "
                         "store.%s" % (judged, n, min_rows, _skip_note)),
                        checked=n, skipped=skipped, judged=judged)
    dead = sorted(k for k in (on_every or ()) if not filled.get(k))
    return {
        "state": "DEAD_FIELDS" if dead else "OK",
        "dead": dead, "checked": n, "skipped": skipped, "judged": judged,
        "fields": sorted(on_every or ()),
        "filled": {k: filled.get(k, 0) for k in sorted(on_every or ())},
        "why": (("%d field(s) present on all %d judged row(s) and filled on NONE: %s. A field that "
                 "never once carried a value is not a field, it is a typo with a comma after it.%s"
                 % (len(dead), judged, ", ".join(dead), _skip_note)) if dead else
                ("every field present on all %d judged row(s) carries a value somewhere.%s"
                 % (judged, _skip_note))),
    }


def state():
    """The heart's reading. -> {"ok", "state", "stores", "dead", "why"}"""
    stores, total_dead = [], 0
    for name, path, key in WATCHED:
        rows, why = _rows_of(path, key)
        r = dead_fields(rows)
        if why and rows is None:
            r["why"] = why
        r["store"] = name
        stores.append(r)
        total_dead += len(r["dead"])
    worst = "OK"
    if any(s["state"] == "DEAD_FIELDS" for s in stores):
        worst = "DEAD_FIELDS"
    elif all(s["state"] == "UNKNOWN" for s in stores) and stores:
        worst = "UNKNOWN"
    # ⚠⚠ REG-553 — THE HEADLINE SAID CLEAN WHILE THE STATE SAID UNKNOWN. Measured with the
    # filesystem broken: `state` came back UNKNOWN, the store's own `why` said "would not read",
    # and the top-level `why` announced *"1 store(s) checked, no field is
    # recorded-but-never-filled"* — a clean bill for a check that never happened. A reader sees the
    # headline. Two sentences on one reading disagreeing is the same defect as a badge and a
    # diagram disagreeing on screen, one object smaller. The headline now reports the UNKNOWN
    # stores first, because that is the fact that changes what the rest of it is worth.
    unknown = [x["store"] for x in stores if x["state"] == "UNKNOWN"]
    if total_dead:
        why = ("%d field(s) across %d store(s) are recorded on every row and filled on none"
               % (total_dead, len(stores)))
    elif unknown:
        why = ("nothing was established for %d of %d store(s) (%s) — that is UNKNOWN, not a clean "
               "bill" % (len(unknown), len(stores), ", ".join(unknown)))
    else:
        why = "%d store(s) checked, no field is recorded-but-never-filled" % len(stores)
    if unknown and total_dead:
        why += (" \u26a0 and nothing was established for %d other store(s) (%s)"
                % (len(unknown), ", ".join(unknown)))
    return {"ok": True, "state": worst, "stores": stores, "dead": total_dead, "why": why}


def main(argv):
    r = state()
    if "--json" in argv:
        print(json.dumps(r, indent=2, sort_keys=True))
        return 0
    print("\nA FIELD RECORDED ON EVERY ROW AND FILLED ON NONE\n")
    for s in r["stores"]:
        print("  %-20s %-12s %s" % (s["store"], s["state"], s["why"]))
        for k in s.get("dead") or []:
            print("     ⚠ %s" % k)
    print("\n  %s\n" % r["why"])
    return 0


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
