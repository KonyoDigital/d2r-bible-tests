# -*- coding: utf-8 -*-
"""TWO VOCABULARIES FOR ONE ITEM — what the VAULT calls it, and what the CHRONICLE calls it.

HIS RULING, 2026-09-15, asked whether a `Latent X` sighting witnesses a bare `X` vault row:

    *"each its own.. for chronicle there is only one name for it.. and for items found or
     stashed or items renewed from the hordaic cube these are their own entity in vault terms"*

So the two ledgers do NOT share a key, and that is deliberate:

    CHRONICLE  — a checklist of the game's items. ONE name per item. Owning any form of a
                 Sunder Charm means the grail line for it is answered.
    VAULT      — a record of the physical things in his stash. `Latent Rotting Fissure`,
                 `Renewed Rotting Fissure` and `Rotting Fissure` are THREE things. He can hold
                 all three at once, and a cube recipe turns one into another.

═══ THE AXIS THIS MODULE IS BUILT ON ══════════════════════════════════════════════════════════

Every difference between two spellings is either IDENTITY or RENDERING, and conflating them is
what has gone wrong in both directions here:

  IDENTITY  (must be kept — folding it MERGES two real things)
      the qualifier: Latent / Renewed / bare

  RENDERING (must be folded — keeping it SPLITS one real thing)
      the base-type tail:  "Renewed Rotting Fissure Grand Charm" is the reader printing the
                           base line under the name. Measured in his own vault_seen.json.
      the apostrophe byte: "Atma's Scarab" vs "Atma’s Scarab". His evidence bank holds
                           BOTH forms today — 54 sightings filed under the typographic one
                           while the owned row uses the ASCII one, so the receipt for a name he
                           genuinely owns answered "nothing banked".

Getting the axis backwards is not cosmetic. Fold the qualifier and a Latent charm silently
witnesses the renewed one he does not own. Split on the apostrophe and 54 real sightings become
invisible. Both were live in the tree when this was written.

═══ THE SAFETY RULE ═══════════════════════════════════════════════════════════════════════════

⚠ A QUALIFIER IS ONLY A QUALIFIER IF WHAT REMAINS IS A REAL ITEM. "Renewed" and "Latent" are
ordinary English words and could open any reader misread. Stripping them blindly would corrupt
names on the way past. So a split is only accepted when the remainder RESOLVES against the
roster — otherwise the name is returned untouched. Same rule for the base-type tail. This is the
`_name_folder` discipline (vault_retro.py) applied to a second axis: correct onto the roster, or
leave alone. Never invent.

⚠ AND THIS MODULE DECIDES NOTHING ABOUT OWNERSHIP. It answers "are these two strings the same
thing" for each ledger's own question. Whether a row is owned stays with the witness gates.
"""
import io
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))

try:
    from console_safe import enable as _console_safe_enable
    _console_safe_enable()
except Exception:
    pass

# Identity-bearing prefixes. Both are real D2R Sunder Charm states: the pre-patch charm reads
# "Latent <name>", and the Horadric Cube renews it. Order matters only for the regex.
QUALIFIERS = ("Latent", "Renewed")

# Rendering-only tails: the base line the reader sometimes prints under the item name.
# Measured in his vault_seen.json: "Renewed Rotting Fissure Grand Charm".
BASE_TAILS = ("Grand Charm", "Large Charm", "Small Charm", "Amulet", "Ring", "Jewel")

_QUAL_RE = re.compile(r"^\s*(%s)\s+(.+)$" % "|".join(QUALIFIERS), re.I)
# The board's own disambiguator: "Athena's Wrath (set piece)", "Crescent Moon (amulet)".
_PAREN_RE = re.compile(r"^(.*?)\s*\(([^()]{1,24})\)\s*$")
_ROSTER = None
_ROSTERS = None


def _roster():
    """Every name the game is known to print, lowercased. Unreadable roster -> empty set, and
    every split is then refused rather than guessed. [[unknown-stays-unknown]]"""
    global _ROSTER
    if _ROSTER is not None:
        return _ROSTER
    out = set()
    for fn, keys in (("unique_roster.json", ("names",)),
                     ("set_roster.json", ("pieces", "sets")),
                     ("runeword_roster.json", ("names",))):
        try:
            with io.open(os.path.join(HERE, fn), encoding="utf-8") as fh:
                d = json.load(fh)
            for k in keys:
                for n in (d.get(k) or []):
                    out.add(fold_rendering(str(n)).lower())
        except Exception:
            continue
    _ROSTER = out
    return out


def _rosters():
    """Which roster(s) each bare name belongs to -> {name: {"unique","set","runeword"}}.

    ⚠ THIS IS WHAT MAKES A PARENTHETICAL SUFFIX DECIDABLE. Measured on his own ledger:
      "Athena's Wrath" is a UNIQUE and nothing else -> "(set piece)" is the board disambiguating
          a row for readability, and folding it recovers 50 real sightings.
      "Crescent Moon" is a UNIQUE **and** a RUNEWORD -> "(amulet)" is the only thing telling the
          two apart. Folding it would let a runeword sighting witness a unique amulet he may not
          own. Same punctuation, opposite meaning, and only a measurement separates them.
    """
    global _ROSTERS
    if _ROSTERS is not None:
        return _ROSTERS
    idx = {}
    for fn, keys, tag in (("unique_roster.json", ("names",), "unique"),
                          ("set_roster.json", ("pieces", "sets"), "set"),
                          ("runeword_roster.json", ("names",), "runeword")):
        try:
            with io.open(os.path.join(HERE, fn), encoding="utf-8") as fh:
                d = json.load(fh)
            for k in keys:
                for nm in (d.get(k) or []):
                    idx.setdefault(fold_rendering(str(nm)).lower(), set()).add(tag)
        except Exception:
            continue
    _ROSTERS = idx
    return idx


def _strip_disambiguator(core):
    """Drop a "(...)" suffix ONLY when the bare name belongs to exactly one roster.

    Ambiguous  -> the suffix is the identity; keep it.
    Unresolved -> nothing to gain and the name is unvalidated; keep it. Never invent.
    """
    m = _PAREN_RE.match(core)
    if not m:
        return core
    bare = m.group(1).strip()
    if not bare:
        return core
    owners = _rosters().get(fold_rendering(bare).lower()) or set()
    return bare if len(owners) == 1 else core


def fold_rendering(name):
    """Collapse the differences that are about PRINTING, never about identity.

    Today that is the apostrophe byte and surrounding whitespace. It deliberately does NOT touch
    case: the rosters are title-cased and callers compare lowercased when they mean to.
    """
    if name is None:
        return ""
    s = str(name)
    # U+2019 RIGHT SINGLE QUOTATION MARK and friends -> ASCII apostrophe. His bank holds both.
    s = s.replace(u"’", "'").replace(u"ʼ", "'").replace(u"´", "'")
    return re.sub(r"\s+", " ", s).strip()


def _strip_tail(core):
    """Drop a base-type tail ONLY when what remains is still a real item."""
    core = _strip_disambiguator(core)
    for t in BASE_TAILS:
        if core.lower().endswith(" " + t.lower()):
            rest = core[: -(len(t) + 1)].strip()
            if rest and fold_rendering(rest).lower() in _roster():
                return rest
    return core


def split_name(name):
    """-> (qualifier, core). qualifier is '' when the name carries none.

    The split is refused unless the remainder is a real item, so an ordinary misread that merely
    starts with the word "Renewed" is returned whole.
    """
    s = fold_rendering(name)
    if not s:
        return "", ""
    s = _strip_tail(s)
    m = _QUAL_RE.match(s)
    if not m:
        return "", s
    qual, rest = m.group(1), m.group(2).strip()
    rest = _strip_tail(rest)
    if rest and fold_rendering(rest).lower() in _roster():
        # canonicalise the qualifier's casing off QUALIFIERS rather than echoing the reader
        for q in QUALIFIERS:
            if q.lower() == qual.lower():
                return q, rest
        return qual, rest
    return "", s


def vault_key(name):
    """What the VAULT calls this thing. The qualifier is KEPT — it is a different object.

    vault_key("Renewed Rotting Fissure Grand Charm") -> "Renewed Rotting Fissure"
    vault_key("Latent Rotting Fissure")              -> "Latent Rotting Fissure"
    vault_key("Rotting Fissure")                     -> "Rotting Fissure"
    """
    qual, core = split_name(name)
    return ("%s %s" % (qual, core)).strip() if qual else core


def chronicle_key(name):
    """What the CHRONICLE calls this thing. ONE name, per his ruling — any form answers the
    grail line."""
    _qual, core = split_name(name)
    return core


def same_vault_entity(a, b):
    """Are these two strings the same physical thing in his stash?"""
    ka, kb = vault_key(a).lower(), vault_key(b).lower()
    return bool(ka) and ka == kb


def same_chronicle_entry(a, b):
    """Do these two strings answer the same grail line?"""
    ka, kb = chronicle_key(a).lower(), chronicle_key(b).lower()
    return bool(ka) and ka == kb


def qualified_forms(core):
    """Every vault entity that shares one chronicle line — for a surface that wants to show him
    the family rather than one row of it."""
    c = fold_rendering(core)
    return [c] + ["%s %s" % (q, c) for q in QUALIFIERS]


if __name__ == "__main__":
    for n in ("Renewed Rotting Fissure Grand Charm", "Latent Rotting Fissure",
              "Rotting Fissure", u"Atma’s Scarab", "Atma's Scarab",
              "Renewed Something That Is Not An Item"):
        print("%-40r vault=%-32r chronicle=%r" % (n, vault_key(n), chronicle_key(n)))
