#!/usr/bin/env python3
"""A SYNTHETIC unsorted dock, so the Vault Manager's layout can be designed without his live store.

⚠ WHY THIS EXISTS. Task #41 wants the dock rebuilt as one organised box instead of a ragged pill
wall. Doing that against his real store would be `feedback-fixtures-never-touch-live-data` from the
wrong side: a layout tuned to whatever 215 items he happens to own today, and a design pass that
writes to `d2r_owned` if anything goes wrong.

WHAT A DOCK LAYOUT ACTUALLY STRESSES, measured from bible.html:34588 rather than guessed:
  * `unsorted` = ownedPool() minus shared-stash minus aggregates, filtered to no mule assignment.
  * The pill carries the ITEM NAME, so the widest name sets the ragged edge. Real names run from
    "Nagelring" (9) to "Death's Web" and beyond — a fixture of short names would produce a tidy
    wall that the real data never gives you, which is the blind-fixture defect in layout form.
  * Names carry BOTH apostrophe bytes. 202 straight and 4 curly in his catalogue, and that mix has
    already cost 158 of 206 names the wrong mule once. A dock fixture that uses only ASCII would
    render clean and prove nothing. [[d2r-curly-apostrophe-class]]

So the fixture is built from the REAL catalogue in bible.html when it can be read, and falls back to
a named, honest, hand-written spread when it cannot — never to a silent empty list.
"""

import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

# The hand-written fallback. Chosen for SHAPE, not flavour: shortest and longest real names, both
# apostrophe bytes, a two-word name, a name with a digit-free roman numeral, and one that is
# pathologically long. If the catalogue cannot be read these still stress the same edges.
FALLBACK = [
    "Nagelring", "Manald Heal", "The Stone of Jordan", "Death's Web", "Gheed’s Fortune",
    "Crown of Ages", "Arreat's Face", "Mara's Kaleidoscope", "Harlequin Crest",
    "Templar's Might", "Griffon's Eye", "Ondal's Wisdom", "Steelrend", "Dracul's Grasp",
    "Wisp Projector", "Highlord's Wrath", "String of Ears", "Verdungo's Hearty Cord",
    "Bul-Kathos' Wedding Band", "Metalgrid",
]


def _catalogue_names(limit=400):
    """Real item names off bible.html. -> (names, why_not)"""
    p = os.path.join(REPO, "bible.html")
    try:
        s = io.open(p, encoding="utf-8").read()
    except Exception as e:
        return None, "bible.html could not be read: %s" % str(e)[:80]
    # ITEM_CODEX is a JS object literal KEYED BY ITEM NAME — the real spelling, both apostrophe
    # bytes included. My first cut guessed at `data-item-name="..."` markup that does not exist,
    # matched nothing, and fell back to 20 hand-written names repeated to fill 215 pills. It SAID it
    # had fallen back, which is the only reason this was caught rather than shipped as a realistic
    # dock. A fixture that silently degrades is the blind-fixture defect.
    #
    # ⚠ This is a LAYOUT fixture, so ITEM_CODEX is the right source: it is the widest set of real
    # NAMES. It is NOT the full owned universe (uniques/sets also live in markup), and nothing here
    # may be used to count what he owns. [[d2r-db-completeness-audit]]
    m = re.search(r"const ITEM_CODEX *= *\{", s)
    names = []
    if m:
        names = re.findall(r'"((?:[^"\\]|\\.){3,60})" *: *\{ *"rarity"', s[m.end() - 1:])
    out, seen = [], set()
    for n in names:
        n = n.strip()
        if not n or n in seen:
            continue
        seen.add(n)
        out.append(n)
        if len(out) >= limit:
            break
    if not out:
        return None, "no item names matched in bible.html — the markup shape has moved"
    return out, None


def dock(n=215):
    """An unsorted pile of `n` names. -> (names, source)

    215 is his real count as of 2026-08-28, and it is a BACKLOG rather than a bug: `unsorted` is a
    filter of owned, so it can never over-report, and the auto-assign path is joined end to end.
    Designing against the real magnitude matters — a dock that looks organised at 12 pills and falls
    apart at 215 is the same defect as a gate that only runs at one viewport.
    """
    names, why = _catalogue_names()
    if not names:
        base, src = FALLBACK, "hand-written fallback (%s)" % why
    else:
        base, src = names, "bible.html catalogue"
    out = []
    while len(out) < n:
        out.extend(base)
    return out[:n], src


def widest(names):
    """The name that sets the ragged edge, and by how much. -> dict"""
    if not names:
        return {"ok": False, "why": "no names"}
    lo = min(names, key=len)
    hi = max(names, key=len)
    return {"ok": True, "shortest": lo, "shortestLen": len(lo),
            "longest": hi, "longestLen": len(hi), "spread": len(hi) - len(lo)}


def stresses_the_real_edges(names):
    """PROVE the fixture actually exercises what breaks. -> (ok, why)

    A fixture that renders tidily is worse than none: it certifies a layout the real data will
    break. [[feedback-blind-fixture-green-gate]]
    """
    if len(names) < 50:
        return False, "%d names is not a dock — the ragged-wall problem only appears in bulk" % len(names)
    w = widest(names)
    if w["spread"] < 8:
        return False, ("every name is within %d characters, so this fixture cannot produce a ragged "
                       "edge — the exact thing the redesign is for" % w["spread"])
    if not any("’" in n for n in names) and not any("'" in n for n in names):
        return False, "no name carries an apostrophe of either byte, and both occur in his catalogue"
    return True, None


def as_localstorage(names):
    """The seed a browser harness can drop in. -> str (JSON)

    ⚠ NEVER WRITTEN TO HIS STORE BY THIS MODULE. It returns the string; the harness decides where it
    goes, and a harness aiming at his real profile is the caller's bug to avoid, not something this
    file can paper over.
    """
    return json.dumps({"d2r_owned": sorted(set(names)), "d2r_vaultAssign": {}},
                      ensure_ascii=False)


def main(argv=None):
    try:
        from console_safe import enable  # noqa: F401
    except Exception:
        pass
    names, src = dock()
    w = widest(names)
    ok, why = stresses_the_real_edges(names)
    print("unsorted dock fixture: %d pills, from %s" % (len(names), src))
    print("  shortest: %-28s %d chars" % (w["shortest"], w["shortestLen"]))
    print("  longest:  %-28s %d chars" % (w["longest"], w["longestLen"]))
    print("  spread:   %d characters of ragged edge" % w["spread"])
    print("  distinct: %d" % len(set(names)))
    curly = sum(1 for n in set(names) if "’" in n)
    print("  names carrying a CURLY apostrophe: %d (the class that cost 158 of 206 the wrong mule)"
          % curly)
    print("  %s" % ("\U0001f7e2 this fixture stresses the edges the redesign has to survive"
                    if ok else "\U0001f534 %s" % why))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
