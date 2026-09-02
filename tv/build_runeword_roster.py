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


def is_stale(path=None, bible_path=None):
    """-> (stale: bool, why: str). A missing or unreadable artifact counts as STALE, never as fine.

    ⚠ v2455 — A21c. THIS LANE DID NOT EXIST, and nothing said so. `build()` stamps `sourceHash`
    into the artifact and that is where the story ended: no function on this machine ever
    recomputed it, and no gate ever asked. Its two siblings both do — `roster_sync.is_stale()` is
    called by a gate in `test_control.py` — so the runeword chronicle was the one route of three
    with no watcher.

    It was not WRONG when this was written: measured 2026-09-03, 105 names, block hash equal,
    nothing on the page missing from the roster and nothing in the roster missing from the page.
    That is the whole point. A lane with no watcher is correct right up until it is not, and the
    day it stops nobody is told — `chronicle_resolve` keeps folding names against a roster the
    page has moved past, and every name it silently fails to canonicalise looks like a name he
    simply does not own. [[the-unjoined-end]] [[unknown-stays-unknown]]

    STAMPING IS NOT CHECKING. `build()` writes the hash; this reads it back and compares.
    """
    path = path or OUT
    bible_path = bible_path or BIBLE
    if not os.path.isfile(path):
        return True, "no runeword roster on disk — nothing to resolve chronicle names against"
    try:
        doc = json.load(io.open(path, encoding="utf-8"))
    except Exception as e:
        return True, "runeword roster will not parse — %s" % str(e)[:70]
    try:
        names, blk = extract(io.open(bible_path, encoding="utf-8").read())
    except Exception as e:
        # the PAGE could not be read. That is UNKNOWN about the page, and reporting it as
        # "in sync" would be a green produced by a broken instrument.
        return True, "could not read RUNEWORDS out of bible.html — %s" % str(e)[:70]
    want = hashlib.sha256(blk.encode("utf-8")).hexdigest()
    got = doc.get("sourceHash")
    if got != want:
        return True, ("bible.html's RUNEWORDS block has changed since the roster was built "
                      "(stamped %s, page now %s) — run: python3 tv/build_runeword_roster.py"
                      % (str(got)[:12], want[:12]))
    if doc.get("count") != len(names):
        return True, ("the roster says %s names and the page yields %d — the stamp matches, so "
                      "the artifact was hand-edited" % (doc.get("count"), len(names)))
    return False, "in sync (%d names)" % len(names)


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
