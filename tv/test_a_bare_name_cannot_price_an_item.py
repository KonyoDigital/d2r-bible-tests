# -*- coding: utf-8 -*-
"""v3368 (#60) — A BARE NAME CANNOT PRICE AN ITEM, AND THE READER WAS THROWING AWAY THE REST.

HIS ASK: route to garbage vs HIGH QUALITY, and he named the case outright — *"even base item with
buffs socketed items"*. Then, giving the vocabulary: *"all these drop socketed item and ethereal
items and base items with or without sockets white/blue/gold/unique/green for set"*.

So a BASE ITEM'S VALUE IS DECIDED BY SOCKETS · ETHEREAL · QUALITY, not by its name. And the
pipeline kept none of the three.

MEASURED 2026-09-19 on his real stores:
    a sighting row's COMPLETE field list   name · lane · kind · witnesses · conf · lastSeenTs
    "socket"/"ethereal"/"quality" across all three vault stores, 44 rows      0 occurrences
    the reader's declared return contract  {name, kind, count, conf, lane, throwOut, throwWhy}

⚠⚠ AND THE READER WAS ALREADY LOOKING. Sockets appear in VAULT_READ_PROMPT — but ONLY as throw-out
criteria ("sockets and no magical text", "white base, no sockets"). So it used them to form a junk
opinion and discarded the fact. A plain `Gorgon Crossbow` and an ethereal 4-socket one arrived as
the SAME ROW, and no price list can ever separate them: the distinguishing information was never
stored. [[heart-first]] §6 — persist what you KNEW, not a summary of it. Third instance of that
exact shape already carved there (the first two: which SURFACE a frame showed, stored as
`{"panel": 1019}`; which FRAMES carried a panel, stored as `{"panels": 18, "frames": 2385}`).

=== WHY THE TEMPLATE, NOT JUST THE PARSER ===
v2011 measured this mechanism on `throwWhy`: it was read by the parser, ABSENT from the prompt's
JSON template, and therefore never emitted — *"a model told to reply with STRICT JSON matching a
template emits the template's keys"*. Adding a parser field without adding the template key builds
a slot nothing will ever fill. Both ends or neither. [[the-unjoined-end]]

=== NULL IS NOT ZERO, AT ALL THREE FIELDS ===
    sockets 0    a MEASUREMENT — the reader saw it has none
    sockets null the reader could not tell
    eth False    visibly not ethereal        eth null   unknown
Collapsing either pair invents a fact about his loot, and these feed a routing decision about what
to throw away. [[unknown-stays-unknown]]

⚠ PRICES ARE DOWNSTREAM OF THIS. An averaged price cannot be applied to a row that does not say
whether the item is socketed — so this lands before the tier, not after.
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import vault_retro as VR  # noqa: E402


def _row(**raw):
    """Parse one reader item the way the sweep really does — through `normalize_item`.

    ⚠ The first cut of this helper called `VR._item_of(...)`, which does not exist. It was guarded
    by `hasattr` so it would have returned None forever instead of raising — a helper that silently
    answers about nothing. Caught by checking the name against the file rather than assuming it.
    """
    return VR.normalize_item(raw, "stash", "stash", 0.9)


class TheTemplateCarriesTheKeys(unittest.TestCase):
    """⚠⚠ v2011's lesson: a key absent from the template is never returned."""

    def _prompt(self):
        src = io.open(os.path.join(HERE, "tv_diablo.py"), encoding="utf-8").read()
        i = src.find("VAULT_READ_PROMPT = (")
        self.assertGreater(i, -1, "VAULT_READ_PROMPT is gone")
        t = src[i:i + 9000]
        return "\n".join(l for l in t.split("\n") if not l.strip().startswith("#"))

    def test_the_three_keys_are_in_the_json_template(self):
        p = self._prompt()
        for k in ('"sockets"', '"eth"', '"quality"'):
            self.assertIn(
                k, p,
                "%s is not in the prompt's JSON template. v2011 measured that a key the parser "
                "reads but the template omits is NEVER EMITTED — that is how throwWhy came back "
                "empty on every row for versions. A parser slot with no template key is a slot "
                "nothing will fill." % k)

    def test_the_prompt_says_null_rather_than_guess(self):
        p = self._prompt()
        self.assertIn(
            "NEVER GUESS", p.upper().replace("NEVER GUESS ANY", "NEVER GUESS"),
            "the prompt no longer forbids guessing these from the icon. A guessed socket count is "
            "banked against his loot and decides whether something is thrown away.")


class NullIsNotZero(unittest.TestCase):

    def test_sockets_absent_is_None_and_zero_is_zero(self):
        """⚠⚠ THE CASE. 0 says 'it has none'; None says 'nobody could tell'."""
        self.assertIsNone(VR._sockets_of(None), "an absent socket count became a number")
        self.assertEqual(VR._sockets_of(0), 0, "a MEASURED zero was discarded")
        self.assertEqual(VR._sockets_of(4), 4)
        self.assertIsNone(VR._sockets_of("banana"), "unparseable became a number")

    def test_sockets_are_bounded_by_the_GAME_not_by_taste(self):
        """Nothing in D2R carries more than 6. A larger number is a misread, not a rare item."""
        self.assertIsNone(VR._sockets_of(7),
                          "7 sockets was accepted. The game cannot produce it, so banking it is a "
                          "claim about his loot that no item can satisfy")
        self.assertEqual(VR._sockets_of(6), 6, "6 is legal and was refused")

    def test_quality_maps_HIS_words_and_refuses_the_rest(self):
        for said, want in (("green", "set"), ("normal", "white"), ("magic", "blue"),
                           ("rare", "gold"), ("unique", "unique"), ("white", "white")):
            self.assertEqual(VR._quality_of(said), want,
                             "%r should read as %r — that is his own vocabulary" % (said, want))
        self.assertIsNone(VR._quality_of("turquoise"),
                          "an unrecognised colour was mapped to a nearest match instead of UNKNOWN")
        self.assertIsNone(VR._quality_of(""), "empty became a colour")


class TheRowCarriesAllThree(unittest.TestCase):

    def test_the_parser_puts_them_on_the_row(self):
        src = io.open(os.path.join(HERE, "vault_retro.py"), encoding="utf-8").read()
        code = "\n".join(l.split("#", 1)[0] for l in src.split("\n"))
        for frag in ('"sockets": _sockets_of(', '"quality": _quality_of(', '"eth":'):
            self.assertIn(
                frag, code,
                "the row no longer carries %s. Computing a fact and dropping it before the row is "
                "this repo's most repeated defect, and here it is the fact his whole "
                "garbage-vs-high-quality ask depends on." % frag)

    def test_eth_keeps_three_states(self):
        src = io.open(os.path.join(HERE, "vault_retro.py"), encoding="utf-8").read()
        code = "\n".join(l.split("#", 1)[0] for l in src.split("\n"))
        self.assertIn(
            'else (False if raw.get("eth") is False else None)', code,
            "eth has collapsed to a bool. `False` means visibly-not-ethereal and `None` means "
            "nobody could tell; a bool cannot hold both and the difference decides a throw-out.")


class ARealRowCarriesTheFactsEndToEnd(unittest.TestCase):
    """⚠ BEHAVIOURAL, not a source grep. The source cases above pin the WIRING; this drives the
    real `normalize_item` and asserts the three facts survive the trip onto the row."""

    def test_a_socketed_ethereal_base_is_no_longer_the_same_row_as_a_plain_one(self):
        rich = _row(name="Gorgon Crossbow", kind="item", sockets=4, eth=True, quality="white")
        plain = _row(name="Gorgon Crossbow", kind="item", sockets=0, eth=False, quality="white")
        self.assertIsNotNone(rich, "normalize_item refused a well-formed item")
        self.assertEqual((rich.get("sockets"), rich.get("eth")), (4, True))
        self.assertEqual((plain.get("sockets"), plain.get("eth")), (0, False))
        self.assertNotEqual(
            (rich.get("sockets"), rich.get("eth")), (plain.get("sockets"), plain.get("eth")),
            "an ethereal 4-socket base and a plain one still produce the same row — which is the "
            "whole defect: no price list can separate them because the row cannot")

    def test_a_reader_that_says_nothing_leaves_all_three_UNKNOWN(self):
        bare = _row(name="Gorgon Crossbow", kind="item")
        self.assertIsNone(bare.get("sockets"), "an unstated socket count became a number")
        self.assertIsNone(bare.get("eth"), "an unstated ethereal flag became a bool")
        self.assertIsNone(bare.get("quality"), "an unstated quality became a colour")


class TheRowSaysWHICHPromptReadIt(unittest.TestCase):
    """⚠⚠ THE CASE THAT CAUGHT A READER WITH NO WRITER, BEFORE IT SHIPPED.

    The heart row for this version counts sightings "read by prompt X" — and MEASURED before this
    was added, `promptVer` appeared ZERO times in vault_seen.json while the sighting row carried
    only name/lane/kind/witnesses/conf/lastSeenTs. So the watcher keyed on a field nothing wrote
    and would have read UNKNOWN forever, while this version's own note claimed "a row records which
    prompt produced it". A claim in a ship note is not a join. [[the-unjoined-end]]

    ⚠ AND IT IS LOAD-BEARING FOR THE NULLS. Rows from vp2017 have null sockets because the prompt
    never asked; rows from vp3368 have null sockets because the reader could not tell. Without the
    stamp those two nulls are the same bytes and the population cannot be named. [[stale-reading]]
    """

    def test_a_parsed_row_records_the_prompt_that_read_it(self):
        r = _row(name="Gorgon Crossbow", kind="item", sockets=4, eth=True, quality="white")
        self.assertIn("promptVer", r,
                      "the row does not say which prompt read it, so a null from the OLD prompt "
                      "and a null from the NEW one are indistinguishable")
        self.assertTrue(str(r.get("promptVer") or "").strip(),
                        "promptVer is present but empty, which names no prompt at all")

    def test_it_matches_the_version_tv_diablo_declares(self):
        import tv_diablo as TD
        r = _row(name="Gorgon Crossbow", kind="item")
        self.assertEqual(
            r.get("promptVer"), getattr(TD, "VAULT_PROMPT_VER", None),
            "the row stamps a version that is not the one the prompt module declares — a remembered "
            "constant attributing rows to a prompt that may not have run")


class TheOldRowsAreNotBackFilled(unittest.TestCase):
    """⚠ His 44 existing rows were read by a prompt that never asked. They must stay UNKNOWN."""

    def test_a_reader_that_says_nothing_yields_None_everywhere(self):
        self.assertIsNone(VR._sockets_of(None))
        self.assertIsNone(VR._quality_of(None))

    def test_the_prompt_version_moved(self):
        src = io.open(os.path.join(HERE, "tv_diablo.py"), encoding="utf-8").read()
        self.assertNotIn(
            'VAULT_PROMPT_VER = "vp2017"', src,
            "the prompt changed and its version did not, so a row cannot say which prompt produced "
            "it — and a null socket count from the OLD prompt is indistinguishable from a null the "
            "new one genuinely could not read. [[stale-reading]]")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "dropping the keys from the template means the model never returns them, however well the parser reads",
        "file": "tv/tv_diablo.py",
        "find": '\'"quality":"white|blue|gold|unique|set|null",\'',
        "replace": "''",
        "matches": 1,
    },
    {
        "why": "collapsing an absent socket count to 0 claims the item has none, which decides a throw-out",
        "file": "tv/vault_retro.py",
        "find": "    if v is None or v is True or v is False:\n        return None",
        "replace": "    if v is None or v is True or v is False:\n        return 0",
        "matches": 1,
    },
    {
        "why": "accepting an out-of-range socket count banks a number the game cannot produce",
        "file": "tv/vault_retro.py",
        "find": "    return n if 0 <= n <= 6 else None",
        "replace": "    return n",
        "matches": 1,
    },
    {
        "why": "dropping the prompt stamp makes an OLD null and a NEW null the same bytes, and leaves the heart row keyed on a field nobody writes",
        "file": "tv/vault_retro.py",
        "find": '        "promptVer": _prompt_ver(),',
        "replace": "",
        "matches": 1,
    },
    {
        "why": "mapping an unrecognised colour to a nearest match invents a quality for his item",
        "file": "tv/vault_retro.py",
        "find": "    return q if q in QUALITIES else None",
        "replace": "    return q or None",
        "matches": 1,
    },
]
