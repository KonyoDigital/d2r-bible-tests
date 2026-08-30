#!/usr/bin/env python3
"""THE HARDCODED LAW ABOUT WHICH ITEMS ARE FURNITURE, AND WHICH ARE NOT LOOT AT ALL.

★ Konyo, 2026-08-30, reading his own session back: "these are locked items though like the super
mana in my inventory isnt.. it will get thrown out... easy... or used.. nothing to really think
about them they suck. and are worthless. but the horadric cube and tome of identify and tome of
town of scrolls portals.. these are locked inventory items within the inventory template thats a
LAW.. check and verify and make this also a unified logic within the ai readers and console. it
needs a hardcode logic".

THREE CLASSES, and the distinction is his:

  LOCKED      Furniture. The Horadric Cube, the tomes, Wirt's Leg, keys. They occupy inventory in
              essentially every frame, they are never a find, and NOTHING should ever suggest
              muling, stashing or throwing them. vault_corpus already calls this shape FIXED:
              "the space that isnt locked for the items like hordaic cube and my other tombs and
              charms.. which again should render this and lock it accordingly like the equipment."

  CONSUMABLE  Potions, rejuvenations, scrolls, gold. His words: "it will get thrown out... easy..
              or used.. nothing to really think about them they suck. and are worthless." Not
              furniture — they come and go — but never worth a register or a paid read.

  LOOT        Everything else. The only class the funnel should spend anything on.

⚠ WHY THIS FILE EXISTS RATHER THAN A FOURTH COPY. The law was ALREADY encoded, correctly, in three
separate places — measured 2026-08-30:
    control_app._REGISTER_ANCHORS   frozenset(horadric cube, wirt's leg, wirts leg, key, tome)
    control_app._register_is_junk   potion / rejuvenation / scroll / gold shapes
    vault_corpus  FIXED/OPEN/CHURN  the same idea as GEOMETRY, naming no items
    tv_diablo:404 the live prompt   names the cube and tomes as ANCHORS in prose
Three encodings of one law is precisely the drift he asked to close, and it was working — 0
furniture registered in 24 hours — so this does NOT change behaviour. It gives the retro readers,
which had none of it, the same answer the console already had. [[copy-drift]]

⚠ AND IT IS DELIBERATELY NOT A ROSTER. It matches on the words D2R itself uses, because a reader
hands us OCR of a tooltip, not a database id. A roster lookup would fail on "Tome oF Identify" and
this must not.
"""
import re

#: Furniture. Never loot, never a find, never a mule suggestion.
LOCKED = (
    "horadric cube",
    "tome of identify",
    "tome of town portal",
    "tome",                 # bare "Tome" — the OCR often loses the suffix
    "wirt's leg",
    "wirts leg",
    "key",
)

#: Comes and goes, and is never worth a register or a paid read.
CONSUMABLE_WORDS = (
    "potion", "rejuvenation", "scroll", "antidote", "thawing", "stamina",
)

LOCKED_CLASS = "locked"
CONSUMABLE_CLASS = "consumable"
LOOT_CLASS = "loot"


def _low(name):
    return " ".join(str(name or "").strip().lower().split())


def is_locked(name):
    """Furniture that lives in the inventory by law. -> bool"""
    low = _low(name)
    if not low:
        return False
    for w in LOCKED:
        # word-boundary, so "Monarch" never matches "arch" and "Key" never matches "Monkey"
        if re.search(r"(?<![a-z])" + re.escape(w) + r"(?![a-z])", low):
            return True
    return False


def is_consumable(name):
    """Potions, scrolls, gold — worthless by his ruling. -> bool"""
    low = _low(name)
    if not low:
        return False
    if low == "gold" or re.fullmatch(r"\d[\d,\.]*\s*gold", low):
        return True
    for w in CONSUMABLE_WORDS:
        if re.search(r"(?<![a-z])" + re.escape(w) + r"(?![a-z])", low):
            return True
    return False


def classify(name):
    """-> (LOCKED_CLASS | CONSUMABLE_CLASS | LOOT_CLASS, why)

    ⚠ LOCKED IS CHECKED FIRST AND THE ORDER IS LOAD-BEARING. "Tome of Town Portal" contains
    "scroll" nowhere but a *Scroll* of Town Portal is a consumable while the TOME is furniture, and
    a reader that saw the two in one line must not have the tome demoted by the word beside it.
    """
    low = _low(name)
    if not low:
        return LOOT_CLASS, "no name — nothing can be classified, so it is treated as loot and the "\
                           "reader downstream decides"
    if is_locked(low):
        return LOCKED_CLASS, "inventory furniture — never a find, never a mule suggestion"
    if is_consumable(low):
        return CONSUMABLE_CLASS, "a consumable — used or thrown out, never worth a register"
    return LOOT_CLASS, ""


def worth_registering(name):
    """Should the funnel spend a register on this? -> (bool, why)"""
    cls, why = classify(name)
    return (cls == LOOT_CLASS), (why or "loot")


def main(argv=None):
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    print("── THE INVENTORY LAW ──")
    for n in ("Horadric Cube", "Tome of Identify", "Tome of Town Portal", "Wirt's Leg",
              "Super Mana Potion", "Scroll of Town Portal", "Gold", "1,240 Gold",
              "Crescent Moon", "Lionheart", "Graverobber's Grand Charm", "Monarch"):
        cls, why = classify(n)
        print("  %-28s %-11s %s" % (n, cls, why))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv))
