# -*- coding: utf-8 -*-
"""REG-1271 (#165) — THE GRAIL SEED HOLDS NO NAME A ONE-SHOT OWNS.

Routine I's family A had one cause that was NOT stale numbers: the v3313 bake (2026-09-18) wrote
Fleshrender, Gloom's Trap and The Diggler into _GRAIL_SEED - the three names bake rule 4 exists to refuse,
because each arrives by its own boot one-shot with its own provenance (v1693: "a second witness would
change what 'honest' means"). v1693:275 had been red ever since, and v1692's "first load applies the two
verified finds, 236 -> 238" could not move, because the seed had already put both there.

The baker's one_shot_owned() scraped quoted strings from a LINE WINDOW anchored on the first and last
mention of two flags; a backup list later named one flag ~36,000 lines earlier and the window swallowed
25,522 strings. It now reads each one-shot's names from its own `chronicleApply({ wouldAdd: ... })`.

  · DRIVEN on the real bible.html: one_shot_owned() returns exactly the twelve applied names.
  · DRIVEN on the real bible.html: every seeded name a one-shot owns is one of the nine the RULING one-shot
    applies (they were in the Chronicle-captured seed before it); nothing else.
  · DRIVEN on a fixture: a flag named far away (the backup-list shape) does not inflate the scan.
RED_PROOF below.
"""
import io
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import bake_seed  # noqa: E402

BIBLE = os.path.join(ROOT, "bible.html")


def _src():
    with io.open(BIBLE, encoding="utf-8") as f:
        return f.read()


def _literal(src, name):
    i = src.index("const %s = " % name)
    a = src.index("{", i)
    depth = 0
    for k in range(a, len(src)):
        if src[k] == "{":
            depth += 1
        elif src[k] == "}":
            depth -= 1
            if depth == 0:
                return json.loads(src[a:k + 1])
    raise AssertionError("could not read %s" % name)


class TheSeedHoldsNoOneShotName(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.src = _src()
        cls.owned = bake_seed.one_shot_owned(cls.src)

    def test_premise_the_scan_finds_exactly_the_twelve(self):
        self.assertEqual(len(self.owned), 12, "one_shot_owned found %d names: %r" % (len(self.owned), sorted(self.owned)[:20]))
        for n in ("Fleshrender", "Gloom's Trap", "The Diggler", "Chance Guards"):
            self.assertIn(n, self.owned)

    def test_the_seed_holds_only_the_ruling_nine(self):
        # The nine the RULING one-shot applies were in the Chronicle-captured seed before it existed (it
        # overrides his un-ticks against the game); Fleshrender, Gloom's Trap and The Diggler have their
        # one-shot as their ONLY witness. (_RULING_SEED is not this set: since v2696 it is the ruling
        # migrations as a give-back seed, The Diggler included.)
        seed = _literal(self.src, "_GRAIL_SEED")
        ruling = bake_seed.one_shot_names_by_flag(self.src).get("d2r_v1693RulingApplied") or set()
        self.assertEqual(len(ruling), 9, "premise: the ruling one-shot applies the nine")
        stray = sorted((set(seed) & self.owned) - ruling)
        self.assertEqual(stray, [], "_GRAIL_SEED holds names a boot one-shot owns (a second witness): %r" % stray)

    def test_every_seeded_name_is_one_the_board_can_count(self):
        # REG-1274 — the floor wrote `Harlequin Crest (Shako)`, a key the resolver calls unknown; the Shako was
        # not counted (measured: found 297 -> 298 once the seed carried `Harlequin Crest`)
        roster = bake_seed.unique_roster(self.src)
        self.assertGreater(len(roster), 400, "premise: the roster was read")
        seed = _literal(self.src, "_GRAIL_SEED")
        off = sorted(n for n in seed if bake_seed._norm_key(n) not in roster)
        self.assertEqual(off, [], "_GRAIL_SEED holds names the board's roster cannot count: %r" % off)

    def test_the_baker_folds_a_vault_spelling_and_refuses_the_unknown(self):
        roster = bake_seed.unique_roster(self.src)
        self.assertEqual(bake_seed.seed_name("Harlequin Crest (Shako)", roster), "Harlequin Crest")
        self.assertEqual(bake_seed.seed_name("Atma\u2019s Scarab", roster) is not None, True)
        self.assertIsNone(bake_seed.seed_name("Naglring", roster), "a misread no roster name matches must not be seeded")

    def test_a_far_flag_does_not_inflate_the_scan(self):
        fixture = ("var bk=['d2r_v1692FleshrenderApplied'];\n" + "x;\n" * 500 +
                   "var s=['Not A One Shot', \"Nor This\"];\n" + "y;\n" * 500 +
                   "window.chronicleApply({ wouldAdd: { uniques: ['Fleshrender', \"Gloom's Trap\"], sets: [] }, lanes: [] });\n"
                   "window.LSR.setItem('d2r_v1692FleshrenderApplied', '1');\n")
        self.assertEqual(bake_seed.one_shot_owned(fixture), {"Fleshrender", "Gloom's Trap"})


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "REG-1274 - the seed carries the vault spelling again: the floor writes a key the tally cannot count",
        "file": "bible.html",
        "find": "\"Harlequin Crest\":\"Sep 16, 2026 · 15:28\",",
        "replace": "\"Harlequin Crest (Shako)\":\"Sep 16, 2026 · 15:28\",",
        "matches": 1,
    },
    {
        "why": "REG-1271 - The Diggler is seeded again: v1693's one-shot is no longer its only witness",
        "file": "bible.html",
        "find": "const _GRAIL_SEED = {",
        "replace": "const _GRAIL_SEED = {\"The Diggler\":\"Jul 27, 2026 · 01:15\",",
        "matches": 1,
    },
    {
        "why": "REG-1271 - the baker stops reading one-shot names: rule 4 refuses nothing again",
        "file": "bake_seed.py",
        "find": "        names |= {x or y for x, y in got if (x or y)}\n",
        "replace": "        pass\n",
        "matches": 1,
    },
]
