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

#: The stores this watches, and WHERE THE ROWS ARE. Deliberately short: he ruled *"I DO NOT want
#: this to randomly just connect wires to it if theres no need"*, so a store earns a line here by
#: having a record somebody acts on, not by existing. `reel_tombstones` is here because it is the
#: permanent record of the ONE action with no undo.
WATCHED = (
    ("reel_tombstones", "reel_tombstones.json", "reels"),
)


def _rows_of(path, key):
    """-> (rows, why). A store that will not read is UNKNOWN, never an empty store."""
    p = os.path.join(HERE, path)
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


def dead_fields(rows, min_rows=MIN_ROWS):
    """Which fields are present on every row and filled on none? -> dict

    A field is DEAD only when it appears on EVERY row (so it is meant to be there) and no row
    carries a value. A field that is merely sometimes-null is a field with sometimes nothing to
    say, which is a different fact and is not reported.
    """
    if rows is None:
        return {"state": "UNKNOWN", "dead": [], "checked": 0,
                "why": "the store could not be read, so no field was judged"}
    n = len(rows)
    if n < min_rows:
        return {"state": "UNKNOWN", "dead": [], "checked": n,
                "why": ("%d row(s) is under the %d-row floor — a column of nulls here is a young "
                        "store, and a zero over rows that cannot disagree measures the sample"
                        % (n, min_rows))}
    on_every, filled = None, {}
    for r in rows:
        keys = set(r.keys())
        on_every = keys if on_every is None else (on_every & keys)
        for k, v in r.items():
            if v is not None and v != "" and v != []:
                filled[k] = filled.get(k, 0) + 1
    dead = sorted(k for k in (on_every or ()) if not filled.get(k))
    return {
        "state": "DEAD_FIELDS" if dead else "OK",
        "dead": dead, "checked": n, "fields": sorted(on_every or ()),
        "filled": {k: filled.get(k, 0) for k in sorted(on_every or ())},
        "why": (("%d field(s) present on all %d row(s) and filled on NONE: %s. A field that never "
                 "once carried a value is not a field, it is a typo with a comma after it."
                 % (len(dead), n, ", ".join(dead))) if dead else
                "every field present on all %d row(s) carries a value somewhere" % n),
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
    return {
        "ok": True, "state": worst, "stores": stores, "dead": total_dead,
        "why": (("%d field(s) across %d store(s) are recorded on every row and filled on none"
                 % (total_dead, len(stores))) if total_dead else
                ("%d store(s) checked, no field is recorded-but-never-filled" % len(stores))),
    }


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
