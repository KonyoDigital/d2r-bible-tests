#!/usr/bin/env python3
"""ONE CONCEPT, MANY RENDERINGS — the join the console has been missing five times over.

⚠⚠ MEASURED, NOT SUSPECTED. Three resolvers exist today and they DISAGREE about the same words:

    input        chronicle_template   route_totals   lane_lock
    set          sets                 set            sets
    runeword     runewords            runeword       runewords
    unique       unique               unique         uniques

Six of nine inputs get two different non-None answers. Each is correct FOR ITS OWN CONSUMERS —
the template's ledger map keys on one form, route_totals.ROUTES on another, lane_lock's surfaces on
a third — so flattening them to one output string would break all three. The defect is not the
disagreement; it is that there is nowhere to ask what they are disagreeing ABOUT.

⚠ THE SAME MISSING PIECE HAS NOW CAUSED FOUR SEPARATE DEFECTS, EACH FOUND BY MEASUREMENT:
  · A1  FLOWING is unreachable — `scored` keys on ORGAN ids, the lookup uses LANE names (v2485)
  · A3  9 MISNAMED cells — the organ watches `runeword`, the surface is `chronicle.runeword`
  · v2480  a tab resolved on one side and not the other — `unique` against `uniques`
  · v2490  the board printed THE ARCHITECTURE ASKS and ARCHITECTURE as two topics
Two of those local alias maps I wrote MYSELF, on the same day, while fixing instances of the
problem. A fifth map would have been the obvious next move and the wrong one.

SO: a concept has ONE identity here, and every surface asks for the FORM IT NEEDS. Nothing is
flattened, nothing changes what a consumer receives; the renderings below reproduce exactly what
each resolver returns today, and tv/test_one_name.py asserts that against the live functions.
[[copy-drift]] [[unknown-stays-unknown]]
"""
import re
import sys

#: The identities. A concept is not a string a surface prints — it is the thing all those strings
#: are about. Adding a spelling here is how a new vocabulary joins, instead of a sixth alias map.
CONCEPTS = ("RUNEWORD", "SET", "UNIQUE")

_SPELLINGS = {
    "RUNEWORD": ("runeword", "runewords", "rw"),
    "SET":      ("set", "sets"),
    "UNIQUE":   ("unique", "uniques", "uni"),
}

#: How each surface says it. These are MEASURED from the live resolvers, not chosen — see the
#: guard. A form that differs from what its consumer keys on is a defect, not a preference.
_FORMS = {
    #            template     route        lane/surface   ledger
    "RUNEWORD": ("runewords", "runeword", "runewords",   None),
    "SET":      ("sets",      "set",      "sets",        "chronicle-sets"),
    "UNIQUE":   ("unique",    "unique",   "uniques",     "chronicle-uniques"),
}
_FORM_IX = {"template": 0, "route": 1, "lane": 2, "ledger": 3}

_LOOKUP = {}
for _c, _spells in _SPELLINGS.items():
    for _s in _spells:
        _LOOKUP[_s] = _c


def concept(name):
    """Any spelling, from any surface -> the concept it is about. -> str | None

    ⚠ None means "not a word I know", which is a DIFFERENT fact from a concept with no rendering
    on some surface. Callers must not collapse them. [[unknown-stays-unknown]]
    """
    if not name:
        return None
    s = str(name).strip().lower()
    if s in _LOOKUP:
        return _LOOKUP[s]
    # a dotted surface name carries its concept in the tail: chronicle.runeword -> runeword
    tail = s.split(".")[-1].strip()
    return _LOOKUP.get(tail)


def form(name, surface):
    """The string THIS surface uses for whatever `name` is about. -> str | None

    Never guesses: an unknown word, an unknown surface, or a concept with no rendering on that
    surface all return None rather than echoing the input back.
    """
    c = concept(name)
    if c is None:
        return None
    ix = _FORM_IX.get(str(surface).strip().lower())
    if ix is None:
        return None
    return _FORMS[c][ix]


def same_thing(a, b):
    """Are these two strings about the same concept? -> bool

    This is the question A1 and A3 could not ask. Two unknowns are NOT the same thing.
    """
    ca, cb = concept(a), concept(b)
    return bool(ca and cb and ca == cb)


def main(argv=None):
    print("ONE CONCEPT, MANY RENDERINGS\n")
    print("%-10s %-12s %-10s %-12s %s" % ("concept", "template", "route", "lane", "ledger"))
    print("-" * 58)
    for c in CONCEPTS:
        print("%-10s %-12s %-10s %-12s %s"
              % (c, _FORMS[c][0], _FORMS[c][1], _FORMS[c][2], _FORMS[c][3]))
    print("\nevery spelling this resolves:")
    for c in CONCEPTS:
        print("   %-10s <- %s" % (c, ", ".join(_SPELLINGS[c])))
    print("\nand the question A1 and A3 could not ask:")
    for a, b in (("chronicle.runeword", "runeword"), ("fleet.sets", "set"),
                 ("roster.unique", "uniques"), ("chronicle.set", "unique")):
        print("   same_thing(%-20s %-10s) -> %s" % (a + ",", b, same_thing(a, b)))
    return 0


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    sys.exit(main(sys.argv[1:]))
