#!/usr/bin/env python3
"""BASE -> SET PIECE, for the pieces he has not found yet.

WHY THIS EXISTS. bible.html already expands a BASE name back to the uniques still to hunt
(`_chUniquesOnBase`, using ITEM_CODEX's per-unique `base`). Konyo asked for the same on the sets
side: *"for F-SETS it should cross reference the items i still dont have so it knows whats left to
find and it can keyword search for it when anaylzing and reading. (JUST LIKE UNQIUES i rememever we
integrated this in some way for it already)"*.

It could not simply be copied, and the reason is the interesting part. **ITEM_CODEX carries a `base`
for only 14 of the 135 set pieces** (measured: 320 entries, 300 unique, 14 set, 6 special). The
uniques mechanism works because every unique has a base recorded; the sets side has no such index
and never did.

⚠ AND THE SLOT SUFFIX IS NOT THE BASE. I claimed earlier that the roster records the base in each
piece's suffix, and that is only sometimes true:

    Taebaek's Glory (ward)              base Ward              — suffix IS the base
    Cow King's Hooves (heavy boots)     base Heavy Boots       — suffix IS the base
    Natalya's Soul (claws)              base Scissors Suwayyah — suffix is a CATEGORY
    Horazon's Secrets (grimoire)        base Occult Codex      — suffix is a CATEGORY
    Immortal King's Soul Cage (armor)   base Sacred Armor      — suffix is a CATEGORY

So a suffix-matching rule would resolve some rows and silently mis-resolve others, which is worse
than resolving none. The mapping is real data and has to be read, not derived.

WHAT IT COVERS, HONESTLY. Only the pieces on a recorded Remaining page — 19 of 135 today. That is
not a limitation in practice: **a base printed on the Remaining page is a piece he does not have, by
definition**, so the missing set is exactly the set worth expanding. A base he already owns needs no
expansion. `coverage()` states the fraction rather than letting a caller assume it is complete.
[[unknown-stays-unknown]] [[stale-reading]]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402

_console_safe_enable()


def build(ledger="sets"):
    """{baseLower: {"base":…, "pieces":[…]}} plus the reading's own stamp, or None if never read."""
    import counter_ledger as _cl
    r = _cl.load(ledger)
    if not r:
        return None
    path = os.path.join(_cl._dir(), r["source"])
    try:
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)
    except Exception:
        return None
    idx = {}
    for row in raw.get("rows") or []:
        if not isinstance(row, dict):
            continue
        base, piece = (row.get("base") or "").strip(), (row.get("piece") or "").strip()
        if not base or not piece:
            continue
        slot = idx.setdefault(base.lower(), {"base": base, "pieces": []})
        if piece not in slot["pieces"]:
            slot["pieces"].append(piece)
    for v in idx.values():
        v["pieces"].sort()
    return {"index": idx, "readAt": r.get("readAt"), "reel": r.get("reel"),
            "count": r.get("count"), "source": r.get("source")}


def coverage(built=None, roster=None):
    """How much of the roster this index can speak for — stated, never assumed."""
    b = built if built is not None else build()
    if not b:
        return {"ok": None, "say": "no Remaining page recorded, so there is no base index at all"}
    if roster is None:
        import chronicle_resolve as _res
        roster = _res.load_set_roster() or {}
    pieces = sum(len(v["pieces"]) for v in b["index"].values())
    total = len(roster)
    return {"bases": len(b["index"]), "pieces": pieces, "rosterTotal": total, "ok": True,
            "say": ("%d base(s) covering %d of %d set pieces — every one of them a piece the game "
                    "says you do not have, which is the only case an expansion is needed for"
                    % (len(b["index"]), pieces, total))}


def main(argv=None):
    argv = list(argv if argv is not None else sys.argv[1:])
    b = build()
    if not b:
        print("no Remaining page on file — no base index.")
        print("⚠ that is 'never read', not 'nothing missing'.")
        return 1
    if "--json" in argv:
        print(json.dumps(b, ensure_ascii=False, sort_keys=True))
        return 0
    print("base index from %s (read %s)" % (b["source"], b["readAt"]))
    print("  %s" % coverage(b)["say"])
    print()
    for k in sorted(b["index"]):
        v = b["index"][k]
        print("  %-24s -> %s" % (v["base"], ", ".join(v["pieces"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
