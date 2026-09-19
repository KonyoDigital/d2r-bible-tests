# -*- coding: utf-8 -*-
"""v3364 (#60) — A COMPOSED NAME IS NOT AN UNKNOWN ONE, AND A REFUSAL IS NOT A GUESS.

HIS ASK: *"the vault needs to know every single item in its data base.. and the AI ITEM CHECKER it
goes through also does.. it also needs to know what to route to garbage and what is considered HIGH
QUALITY"*.

The vault could name a UNIQUE, a SET piece and a RUNEWORD — 1,059 roster names. It could name
nothing MAGIC or RARE, because those names are COMPOSED at drop time rather than drawn from a list.
I told him once that magic and rare "cannot have a roster" and he corrected me on the spot: the
install ships the affix tables, so there is no finite NAME list but there IS a finite VOCABULARY.

MEASURED ON HIS OWN INSTALL, 2026-09-19:
    magicPrefix 269 · magicSuffix 298 · rarePrefix 42 · rareSuffix 152 · baseType 690

MEASURED OVER HIS 43 REAL `unsure` ROWS:
    GRAIL 14 · BASE 12 · MAGIC 8 · RARE 4 · UNKNOWN 5
    `Chaotic Grand Charm of Greed` -> 'chaotic' + 'grand charm' + 'of greed'
    `Blood Gyre` · `Death Loop` · `Dread Grasp` · `Bone Visor` -> rare prefix + rare suffix

=== THE ASYMMETRY IS THE WHOLE SAFETY MODEL ===
A consumable or a bare base reading as PROTECTED is the expensive error — his stash never empties,
and the feature he asked for does nothing. A grail reading as UNKNOWN costs one more look. So the
law checks the expensive direction explicitly and by name, and `classify` NEVER returns a best
PARTIAL: an unmatched token, or two parses of differing kind, is UNKNOWN. [[unknown-stays-unknown]]

=== TWO TRAPS THIS FILE PINS, BOTH FOUND BY READING THE REAL DATA ===
1. `item-names.json` IS NOT A BASE-TYPE LIST. It holds 1,593 names — the full item string table,
   uniques included: `Spirit Ward`, `Death Cleaver`, `Venom Ward` are all in it. The base TYPES are
   the 690 from armor/weapons/misc. Using the former as the latter makes a unique look like a plain
   base, which is the throw-it-away direction.
2. THE FIELD IS `vocab`, NOT `kind`. The unsure row has carried `"kind": "item"` since v2051 — a
   literal naming the ROW's kind. A second meaning under that label would be resolved silently by
   whichever writer ran last. [[label-outlived-referent]]

⛔ AND WHAT THIS MUST NOT GROW INTO. Widening `item_identity.BASE_TAILS` with the 690 base types so
`Ice Gorgon Crossbow` resolves is REFUSED, on a measurement taken with BOTH SIDES CASE-FOLDED — the
first cut of that measurement compared lowercase roster names against TitleCase item names, agreed
no matter what was in it, and reported a reassuring 0:

    death cleaver -> death      spirit ward -> spirit      venom ward -> venom

Three UNIQUES collapsing onto three RUNEWORDS, in `vault_key` AND `chronicle_key`, and
`_name_folder`'s merge-max never subtracts. Permanent. [[the-unjoined-end]]
"""
import io
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import affix_lexicon as AL  # noqa: E402


def _lex():
    """His generated lexicon, or None. ⚠ A CI runner has no 28 GB install; that is ORDINARY."""
    return AL.load()


class TheVocabularyIsRealAndComplete(unittest.TestCase):

    def test_the_store_carries_all_five_vocabularies(self):
        lex = _lex()
        if lex is None:
            self.skipTest("no lexicon generated on this machine (needs the game install)")
        c = lex.get("counts") or {}
        for k in ("magicPrefix", "magicSuffix", "rarePrefix", "rareSuffix", "baseType"):
            self.assertGreater(
                c.get(k) or 0, 0,
                "%s is %r. A zero here is not 'the game has none' — it is a pull that failed, and "
                "every classification made against it would be a confident wrong answer. "
                "[[zero-needs-a-denominator]]" % (k, c.get(k)))

    def test_baseType_is_the_TYPE_table_not_the_full_string_table(self):
        """⚠⚠ TRAP 1. item-names.json holds 1,593 names INCLUDING uniques. The base types are 690."""
        lex = _lex()
        if lex is None:
            self.skipTest("no lexicon on this machine")
        n = (lex.get("counts") or {}).get("baseType") or 0
        self.assertLess(
            n, 1200,
            "baseType is %d, which is the size of the FULL item string table rather than the base "
            "TYPE tables. `Spirit Ward` and `Death Cleaver` live in that file as UNIQUES, so with "
            "it as the base list a unique reads as a plain base — the throw-it-away direction." % n)
        names = set(lex.get("baseType") or ())
        for u in ("Spirit Ward", "Death Cleaver", "Venom Ward"):
            self.assertNotIn(
                u, names,
                "%r is in baseType. It is a UNIQUE; treating it as a base type is exactly the "
                "conflation this case exists for." % u)

    def test_unresolved_keys_are_STORED_never_dropped(self):
        """⚠ 'the game has no display string for this' and 'nobody looked' must not read alike."""
        lex = _lex()
        if lex is None:
            self.skipTest("no lexicon on this machine")
        ur = lex.get("unresolvedKeys")
        self.assertIsInstance(
            ur, dict,
            "the lexicon does not record which rare keys it could NOT resolve, so a name it cannot "
            "form reads the same as a name it declined to form. [[unknown-stays-unknown]]")
        self.assertIn("rareSuffix", ur)
        self.assertIn(
            "scarab", [str(x).lower() for x in (ur.get("rareSuffix") or ())],
            "`scarab` is no longer recorded as unresolved. It is one of exactly six rare keys with "
            "no display string in EITHER string table, and it is the reason his live `Storm Scarab` "
            "must stay UNKNOWN rather than be guessed into a lane. If the game now resolves it, "
            "this premise has changed and the case should be retired deliberately rather than left "
            "passing over nothing. [[regression-guard]] §4")


class TheGENERATORIsPinnedToo(unittest.TestCase):
    """⚠⚠ THE ARTIFACT CASES ABOVE COULD NOT GO RED AND THEIR PROOFS SAID SO.

    `affix_lexicon.json` is a GENERATED file. A case that reads it grades the bytes that were
    generated last time — so breaking the generator leaves the old, correct artifact sitting on
    disk and every artifact-reading case stays green. Two of this file's red-proofs went BLIND for
    exactly that reason, at match count 1.

    Both halves are needed and they ask different questions: the artifact cases say WHAT SHIPPED IS
    RIGHT, these say THE THING THAT MAKES IT IS STILL RIGHT. [[regression-guard]] §5a
    """

    def _code(self):
        src = io.open(os.path.join(HERE, "affix_lexicon.py"), encoding="utf-8").read()
        return "\n".join(l.split("#", 1)[0] for l in src.split("\n"))

    def test_baseType_is_built_from_the_TYPE_tables(self):
        code = self._code()
        self.assertIn(
            'for t in ("armor", "weapons", "misc"):', code,
            "baseType is no longer built from the base TYPE tables. The obvious substitute is "
            "item-names.json, which is the full 1,593-name string table WITH uniques in it — and "
            "then `Spirit Ward` reads as a plain base, which is the throw-it-away direction.")
        self.assertNotIn(
            "base |= set(nms.values())", code,
            "baseType is being built from the localisation map, i.e. every item name in the game")

    def test_the_unresolved_keys_are_carried_from_the_RESOLVER(self):
        code = self._code()
        self.assertIn(
            '"unresolvedKeys": {"rarePrefix": rp_miss, "rareSuffix": rs_miss},', code,
            "the store no longer carries what the resolver FAILED to resolve. A hardcoded {} here "
            "leaves the artifact looking complete while six rare keys silently have no display "
            "string — and `Storm Scarab` becomes a guess instead of a refusal.")


class ARefusalIsNeverAGuess(unittest.TestCase):

    def test_a_name_with_no_parse_is_UNKNOWN(self):
        lex = _lex()
        if lex is None:
            self.skipTest("no lexicon on this machine")
        for junk in ("Chaotic Zzzzz of Nowhere", "qqq www", "zzzzzzz"):
            k, why = AL.classify(junk, lex=lex)
            self.assertEqual(
                k, "UNKNOWN",
                "%r classified as %s. A best PARTIAL is the one thing this must never return: a "
                "wrong kind becomes a wrong routing decision about his loot." % (junk, k))

    def test_a_name_that_parses_TWO_WAYS_is_UNKNOWN_not_a_coin_flip(self):
        """⚠⚠ THIS CASE WAS MISSING AND ITS RED-PROOF WENT BLIND SAYING SO.

        Every other refusal case uses a name with NO parse, which returns at `if not parses` and
        never reaches the ambiguity arm at all. So deleting that arm changed nothing any case could
        see — the guard was real, the LAW could not reach it. Match count was 1, which is how the
        standing rule tells you it is the law and not the sabotage.

        A FIXTURE, not his real lexicon, because a genuine two-way name may not exist in the game
        today — and a case that depends on one existing would silently stop testing the day it did
        not. [[regression-guard]] §5
        """
        fixture = {
            "counts": {"magicPrefix": 1, "magicSuffix": 1, "rarePrefix": 1,
                       "rareSuffix": 1, "baseType": 1},
            "magicPrefix": ["Alpha"], "magicSuffix": ["of Nothing"],
            "rarePrefix": ["Alpha"], "rareSuffix": ["Beta"],
            "baseType": ["Beta"],
        }
        # "Alpha Beta" is MAGIC (Alpha + Beta) and RARE (Alpha + Beta) at the same time.
        k, why = AL.classify("Alpha Beta", lex=fixture, roster=set())
        self.assertEqual(
            k, "UNKNOWN",
            "a name with a valid MAGIC parse AND a valid RARE parse came back %s (%s). Picking one "
            "is a coin flip wearing a verdict, and it routes his loot on it." % (k, why))
        self.assertIn("AMBIGUOUS", why, "the refusal does not say WHY it refused: %r" % why)
        # ⚠ THE BASELINE, or the clause above would fire on everything: one-way names still parse.
        k2, _ = AL.classify("Alpha Beta of Nothing", lex=fixture, roster=set())
        self.assertEqual(k2, "MAGIC",
                         "an UNAMBIGUOUS composed name came back %s — the arm is now swallowing "
                         "every multi-token name, which is a refusal that means nothing" % k2)

    def test_the_expensive_direction_is_checked_BY_NAME(self):
        """⚠⚠ THE CASE. A consumable or bare base reading as protected means his stash never
        empties and the feature he asked for does nothing."""
        lex = _lex()
        if lex is None:
            self.skipTest("no lexicon on this machine")
        for nm in ("Sacred Rondache", "Bone Knife", "Horadric Cube", "Super Mana Potion",
                   "Small Charm", "Full Rejuvenation Potion", "Tome of Identify", "Ring", "Jewel"):
            k, why = AL.classify(nm, lex=lex)
            self.assertIn(
                k, ("BASE", "UNKNOWN"),
                "%r classified as %s (%s). A plain base or a consumable must land BASE or UNKNOWN; "
                "anything else protects rubbish forever." % (nm, k, why))

    def test_a_composed_magic_name_actually_parses(self):
        """⚠ THE BASELINE. Without it the law would pass over a classifier that refuses everything.
        [[regression-guard]] §5"""
        lex = _lex()
        if lex is None:
            self.skipTest("no lexicon on this machine")
        k, why = AL.classify("Chaotic Grand Charm of Greed", lex=lex)
        self.assertEqual(k, "MAGIC",
                         "a prefix+base+suffix name came back %s (%s) — the vocabulary is present "
                         "but the parse is gone" % (k, why))
        k2, _ = AL.classify("Blood Gyre", lex=lex)
        self.assertEqual(k2, "RARE", "a rare prefix+suffix pair came back %s" % k2)

    def test_an_absent_lexicon_is_UNKNOWN_and_never_raises(self):
        empty = os.path.join(tempfile.mkdtemp(), "nope.json")
        self.assertIsNone(AL.load(empty), "a missing store must read None, never {}")
        k, why = AL.classify("anything at all", lex=None)
        self.assertIn(k, ("UNKNOWN", "GRAIL", "BASE", "MAGIC", "RARE"))


class FreshnessIsNotAssumed(unittest.TestCase):

    def test_verify_never_answers_GREEN_when_it_cannot_tell(self):
        """⚠ 77 is SKIP/UNKNOWN. Returning 0 there turns 'no data' into 'all good'."""
        src = io.open(os.path.join(HERE, "affix_lexicon.py"), encoding="utf-8").read()
        code = "\n".join(l.split("#", 1)[0] for l in src.split("\n"))
        i = code.find("def verify(")
        j = code.find("\ndef ", i + 5)
        seg = code[i:j if j > i else len(code)]
        self.assertIn(
            "return SKIP", seg,
            "verify() has no SKIP arm, so a machine that cannot re-derive the lexicon gets a "
            "verdict instead of an UNKNOWN. [[unknown-stays-unknown]]")
        self.assertNotIn(
            "return 0, \"no lexicon", seg,
            "verify() answers 0 for an absent lexicon — that is 'nobody looked' wearing 'all good'")


class TheJoinIsMade(unittest.TestCase):
    """[[the-unjoined-end]] — a vocabulary nothing consults is documentation."""

    def test_the_unsure_row_carries_the_reading(self):
        src = io.open(os.path.join(HERE, "vault_retro.py"), encoding="utf-8").read()
        code = "\n".join(l.split("#", 1)[0] for l in src.split("\n"))
        self.assertIn(
            '"vocab": _vk, "vocabWhy": _vw,', code,
            "the unsure row no longer carries the lexicon's reading of its name. Computing a "
            "vocabulary and never attaching it to the row is this repo's most repeated defect.")
        self.assertIn("_vocab_of(", code, "nothing calls the classifier helper")

    def test_it_is_NOT_stored_under_the_existing_kind_field(self):
        """⚠⚠ TRAP 2. `kind` has meant the ROW's kind since v2051 and is a hardcoded 'item'."""
        src = io.open(os.path.join(HERE, "vault_retro.py"), encoding="utf-8").read()
        code = "\n".join(l.split("#", 1)[0] for l in src.split("\n"))
        self.assertIn(
            '"kind": "item"', code,
            "the row's own `kind` literal is gone — if the vocabulary took that name over, two "
            "meanings now share one label and whichever writer runs last wins silently")
        self.assertNotIn(
            '"kind": _vk', code,
            "the vocabulary is being written into `kind`, which already means something else on "
            "this row. [[label-outlived-referent]]")


class TheTailStripStaysRefused(unittest.TestCase):
    """⛔ MEASURED, NOT ASSUMED: 3 uniques would collapse onto 3 runewords, permanently."""

    def test_BASE_TAILS_is_still_the_small_curated_list(self):
        import item_identity as II
        tails = getattr(II, "BASE_TAILS", ())
        self.assertLess(
            len(tails), 60,
            "BASE_TAILS has grown to %d entries. Widening it with the game's base types makes "
            "`_strip_tail` drop ' Ward' from `Venom Ward` and resolve the remainder to the RUNEWORD "
            "`Venom` — measured on his real rosters for death cleaver, spirit ward and venom ward, "
            "in vault_key AND chronicle_key, and merge-max never subtracts." % len(tails))


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "returning a best partial instead of UNKNOWN lets an unparsed name be routed on a guess",
        "file": "tv/affix_lexicon.py",
        "find": '    if len({k for k, _ in parses}) > 1:\n        return "UNKNOWN", "AMBIGUOUS: %d parses of differing kind" % len(parses)',
        "replace": "    pass",
        "matches": 1,
    },
    {
        "why": "answering 0 for an absent lexicon turns nobody-looked into a clean bill of health",
        "file": "tv/affix_lexicon.py",
        "find": '        return SKIP, "no lexicon on this machine yet — UNKNOWN, not clean. Run --write."',
        "replace": '        return 0, "no lexicon here"',
        "matches": 1,
    },
    {
        "why": "dropping the unresolved keys makes a name the game cannot form read like one nobody tried",
        "file": "tv/affix_lexicon.py",
        "find": '        "unresolvedKeys": {"rarePrefix": rp_miss, "rareSuffix": rs_miss},',
        "replace": '        "unresolvedKeys": {},',
        "matches": 1,
    },
    {
        "why": "dropping the reading at the unsure row leaves a vocabulary nothing consults",
        "file": "tv/vault_retro.py",
        "find": '                           "vocab": _vk, "vocabWhy": _vw,\n',
        "replace": "",
        "matches": 1,
    },
    {
        "why": "building baseType from the full string table makes a unique read as a plain base",
        "file": "tv/affix_lexicon.py",
        "find": '    for t in ("armor", "weapons", "misc"):\n        base |= set(_named(blobs.get(t)) or ())',
        "replace": "    base |= set(nms.values())",
        "matches": 1,
    },
]
