"""Regenerate runeword_roster.json from bible.html's own `const RUNEWORDS`.

WHY. `unique_roster.json` and `set_roster.json` existed; runewords had no roster at all, so every
check of "is this a real item?" silently answered NO for all 101 of them. Measured 2026-08-31:
the learner rejected `Wrath`, `Peace`, `Bramble` and `Unbending Will` as garbage - real runewords,
read correctly off his runewords Chronicle.

⚠ That gap also means any precision figure computed against uniques+sets alone UNDERSTATES how
well the readers do on chronicle pages, because a runewords chronicle scores zero by construction.

BOTH FORMS ARE KEPT. The roster row is `Spirit (sword)`; a chronicle page prints `Spirit`. A
roster that only holds the qualified form fails on the very surface it is meant to check.
"""

import hashlib
import io
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
BIBLE = os.path.join(os.path.dirname(HERE), "bible.html")
OUT = os.path.join(HERE, "runeword_roster.json")


def extract(src):
    """-> (names, source_block). Raises if the declaration is not found - a generator that
    silently writes an empty roster is worse than one that stops."""
    i = src.index("const RUNEWORDS = [")
    j = src.index("\n];", i)
    blk = src[i:j]
    declared = re.findall(r'\{\s*n:\s*"([^"]+)"', blk)
    if not declared:
        raise ValueError("const RUNEWORDS was found but holds no `n:` entries")
    names = set()
    for n in declared:
        names.add(n.strip())
        bare = re.sub(r"\s*\([^)]*\)\s*$", "", n).strip()
        if bare:
            names.add(bare)
    return sorted(names, key=lambda x: x.lower()), blk


def build():
    src = io.open(BIBLE, encoding="utf-8").read()
    names, blk = extract(src)
    doc = {
        "_comment": "GENERATED from bible.html's const RUNEWORDS by tv/build_runeword_roster.py. "
                    "Both the qualified name and its bare form are kept.",
        "sourceHash": hashlib.sha256(blk.encode("utf-8")).hexdigest(),
        "count": len(names),
        "names": names,
    }
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(doc, indent=1, ensure_ascii=False))
    return doc


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    d = build()
    print("wrote %s — %d name(s)" % (os.path.basename(OUT), d["count"]))
