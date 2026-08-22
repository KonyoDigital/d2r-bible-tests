#!/usr/bin/env python3
"""v1973 — A COUNT IN A COMMENT IS A NUMBER NOBODY RE-MEASURES. NOW SOMETHING DOES.

bible.html says this about itself, twice, in its own words — and then went stale exactly that way
FIVE times in one day (2026-08-22):

  REG-321  a header claimed NINE misread slips; the code made four, and named a candidate it
           never picks.
  REG-323  a spec assertion still said `toBeLessThanOrEqual(2)` after the bound became 3 — CI
           caught it — and a length pre-filter still hardcoded 3, which would have capped reach
           SILENTLY if the bound ever rose.
  REG-326  the roster block claimed `514 − 127 = 387` while naming v659_grail_seed.spec.ts as its
           authority; that spec pins 398. Stale since v1720.
  (this)   the shopping-list comment says "between the chronicle and 99/99" with 100 runewords live.

WHY A GATE AND NOT MORE PROSE. Each of those was written by someone who had just measured. The
warning was already there and was already believed. What was missing is the thing that fails.

WHAT IT DELIBERATELY DOES NOT DO — and this is most of the design:

Most numbers near the word "set pieces" are DIFFERENT QUANTITIES, all correct at once. Measured on
this file: 108 = set pieces in his found ledger · 110 = the same in the 346-key d2r_foundLog ·
127 = union members that are set-piece names · 135 = the roster total. A gate that flagged "four
different counts for one thing" would be wrong four times and get switched off. Same for "14 bosses"
in a perf estimate that says "≈", and "11 bosses" meaning how many drop a Shako.

So this checks ONLY claims that name their subject unambiguously, against a value parsed from the
same file. Each is a pair the author intended to be equal. Adding a check here is cheap; adding a
FUZZY one would be how this gate becomes furniture.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import console_safe
    console_safe.enable()
except Exception:
    pass

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _block(text, name, opener):
    """The literal assigned to `name`, matched by brace/bracket depth rather than a regex —
    these arrays contain both braces and strings, so a non-greedy regex silently truncates."""
    m = re.search(re.escape(name) + r"\s*=\s*" + re.escape(opener), text)
    if not m:
        return None
    start = m.end() - 1
    close = "]" if opener == "[" else "}"
    depth = 0
    for j in range(start, len(text)):
        c = text[j]
        if c == opener:
            depth += 1
        elif c == close:
            depth -= 1
            if depth == 0:
                return text[start:j + 1]
    return None


def _runewords(h):
    lit = _block(h, "RUNEWORDS", "[")
    if not lit:
        return None
    names = re.findall(r'\{\s*n:"([^"]+)"', lit)
    # DISTINCT words, not entries: `Spirit (sword)` and `Spirit (shield)` are one runeword in two
    # bases, and the user-facing denominator counts words. 101 entries, 100 words.
    return len({re.sub(r"\s*\([^)]*\)\s*$", "", n) for n in names})


def _item_value_keys(h):
    lit = _block(h, "window.ITEM_VALUE", "{")
    return len(re.findall(r'"([^"\\]{2,60})"\s*:', lit)) if lit else None


def _uni_extra_keys(h):
    lit = _block(h, "_UNI_EXTRA", "{")
    return len(re.findall(r'"([^"\\]{2,60})"\s*:', lit)) if lit else None


CHECKS = [
    # (label, measure, regex whose group(1) is the claimed number, what the pair means)
    ("runeword denominator", _runewords, r"chronicle and (\d{2,3})/\d{2,3}",
     "the shopping list's 'N/N' is every runeword made"),
    ("ITEM_VALUE keys", _item_value_keys, r"ITEM_VALUE \((\d{3}) keys",
     "the roster's first source"),
    ("_UNI_EXTRA keys", _uni_extra_keys, r"_UNI_EXTRA \((\d{2,3}) keys",
     "the roster's second source"),
]


def main():
    path = os.path.join(REPO, "bible.html")
    h = io.open(path, encoding="utf-8", errors="replace").read()
    bad = []
    checked = 0
    for label, measure, pat, meaning in CHECKS:
        measured = measure(h)
        if measured is None:
            bad.append("%s: could not MEASURE it — the parser missed its literal, which is a "
                       "broken gate, not a passing one" % label)
            continue
        claims = sorted({int(x) for x in re.findall(pat, h)})
        if not claims:
            # No claim is fine: the gate guards claims that exist, it does not demand them.
            continue
        checked += len(claims)
        for c in claims:
            if c != measured:
                bad.append("%s: a comment claims %d, the file measures %d (%s)"
                           % (label, c, measured, meaning))
    if bad:
        print("comment-count: %d stale claim(s)." % len(bad))
        for b in bad:
            print("               " + b)
        print("               Fix the COMMENT (or the data), then re-run. A count in a comment is a")
        print("               number nobody re-measures — this file says so twice and still drifted")
        print("               five times in one day.")
        return 1
    print("comment-count: OK - %d claim(s) match what the file measures." % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
