# -*- coding: utf-8 -*-
"""v3327 — A SEEDED NAME IS NEVER ONE THE GAME SAYS HE LACKS, AND A BULK STAMP IS NOT A FIND.

`_SET_SEED` ships first-found dates into `bible.html`, and a push to main PUBLISHES. MEASURED
2026-09-18 on the live file: 17 of its 133 names are on the game's own Remaining list — pieces he
does not have, carrying dates saying when he found them.

ATTRIBUTED BY BISECT across seven ships: v3308/09/10/11/12 all read 108 seeded / 0 contradictions;
12bcb40c (v3313+v3314) reads 133 / 17. Neither bake_seed.py nor test_bake_seed.py changed in that
range, so the gate went red on DATA.

ROOT CAUSE, PROVEN BY ELIMINATION rather than asserted:
  · bake() rule 3 is `for n in sp_set: if n in missing: continue` — the baker CANNOT add a
    Remaining name.
  · `_SET_MISSING` is untouched by that commit, and the Remaining list measures 19 at every ref
    from v3308 to v3318.
  ⟹ no run of bake() produced these. The literal was HAND-WRITTEN, past the baker's rules.

⚠ AND IT IS ONE-WAY: bake() asserts `set(old_set) <= set(new_set)` ("the bake would LOSE set
names"), so re-baking can never remove a contaminated name. The tool that owns the seed cannot
clean the seed. That is why this is a law over the DATA and not a law over the writer — a source
law cannot see a hand edit, and the only durable guard is one that judges the artefact whoever
wrote it. [[the-unjoined-end]]

THE DISTINCTION IS THE LAW, AND GETTING IT WRONG DELETES HIS REAL FINDS:

  · 15 names shared ONE stamp, "Sep 16, 2026 · 15:28", and ALL FIFTEEN are on the Remaining list.
    Fifteen set pieces are not found in one minute. A stamp shared that widely is a bulk default
    wearing a date — UNDATABLE, and it may never be seeded. [[unknown-stays-unknown]]

  · 2 names are on the Remaining list carrying their OWN distinct dates (Laying of Hands Aug 24 ·
    01:10, Taebaek's Glory Aug 23 · 17:46). These are NOT automatically wrong: "first found" is a
    historical positive and Remaining is present ownership, so found-then-sold satisfies both.
    [[stale-reading]] §8 — never compare a positive and a negative observation as flat set
    membership. They are DECLARED in bake_seed.SEED_EXEMPT with a reason, never silently stripped.

So the law is: a seeded name on the Remaining list must be DECLARED, and a declared name must carry
its own date. A bulk-stamped name can satisfy neither.
"""
import io
import json
import os
import re
import sys
import unittest
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import bake_seed  # noqa: E402

BIBLE = os.path.join(ROOT, "bible.html")

#: A stamp this many pieces share is a bulk write, not a sequence of finds.
BULK_AT = 5


def _seed(src, key):
    m = re.search(r"const %s = (\{.*?\});" % key, src, re.S)
    return json.loads(m.group(1)) if m else None


class TestASeededNameIsNeverOneTheGameSaysHeLacks(unittest.TestCase):

    def setUp(self):
        with io.open(BIBLE, encoding="utf-8") as fh:
            self.src = fh.read()
        # A zero needs a denominator: a truncated read would make every count meaningless.
        self.assertGreater(len(self.src), 5000000,
                           "bible.html read back only %d chars — refusing to judge a seed from a "
                           "file that did not load. [[zero-needs-a-denominator]]" % len(self.src))
        self.missing = set(bake_seed.game_says_missing(self.src))
        self.assertTrue(
            self.missing,
            "the game's Remaining list is EMPTY, so every check below would pass by measuring "
            "nothing. That is UNMEASURED, not clean.")

    def test_no_seeded_name_on_the_remaining_list_is_undeclared(self):
        """THE LAW. Contamination must be declared with a reason, or it is not allowed in."""
        exempt = dict(getattr(bake_seed, "SEED_EXEMPT", {}) or {})
        bad = {}
        for key in ("_SET_SEED", "_GRAIL_SEED"):
            seed = _seed(self.src, key)
            self.assertIsNotNone(seed, "%s is gone from bible.html" % key)
            self.assertTrue(seed, "%s is empty — nothing was measured" % key)
            for n in sorted(set(seed) & self.missing):
                if n not in exempt:
                    bad.setdefault(key, []).append("%s (%s)" % (n, seed[n]))
        self.assertEqual(
            bad, {},
            "seeded name(s) sit on the game's own Remaining list with no declaration:\n  %s\n"
            "A first-found date for a piece he does not have is a fabricated fact on a page he "
            "acts on, and a push to main PUBLISHES it. Either remove the name, or declare it in "
            "bake_seed.SEED_EXEMPT with the reason it is legitimate (found-then-sold is one). "
            "MEASURED 2026-09-18: 17 such names shipped, 15 of them sharing one timestamp."
            % "\n  ".join("%s: %s" % (k, ", ".join(v)) for k, v in sorted(bad.items())))

    def test_a_bulk_stamp_can_never_be_declared_legitimate(self):
        """⚠ THE HALF THAT STOPS THE DECLARATION BECOMING A LOOPHOLE."""
        exempt = dict(getattr(bake_seed, "SEED_EXEMPT", {}) or {})
        seed = _seed(self.src, "_SET_SEED") or {}
        stamps = Counter(seed.values())
        bulk = {s for s, c in stamps.items() if c >= BULK_AT}
        offenders = sorted(n for n in exempt if n in seed and seed[n] in bulk)
        self.assertEqual(
            offenders, [],
            "%d declared name(s) carry a stamp shared by %d+ pieces: %s\n"
            "A shared stamp is a bulk write, so the date cannot be ordered against anything and "
            "the name is UNDATABLE. Declaring one legitimises exactly the 15 that shipped on "
            "'Sep 16, 2026 · 15:28'. Remove it instead." % (len(offenders), BULK_AT, offenders))

    def test_every_declaration_carries_a_reason(self):
        """A declaration with no reason is a silencer wearing a guard's clothes."""
        exempt = dict(getattr(bake_seed, "SEED_EXEMPT", {}) or {})
        empty = sorted(n for n, why in exempt.items() if not str(why or "").strip())
        self.assertEqual(
            empty, [],
            "%d declaration(s) carry no reason: %s. A name is allowed to stay only because "
            "someone can say WHY, and an unexplained exemption is how a list grows silently."
            % (len(empty), empty))

    def test_the_declared_names_are_still_really_there(self):
        """⚠ A declaration for a name that has since gone is a stale permission nobody reads."""
        exempt = dict(getattr(bake_seed, "SEED_EXEMPT", {}) or {})
        if not exempt:
            self.skipTest("nothing is declared — there is no stale permission to find")
        seed = dict(_seed(self.src, "_SET_SEED") or {})
        seed.update(_seed(self.src, "_GRAIL_SEED") or {})
        ghosts = sorted(n for n in exempt if n not in seed)
        self.assertEqual(
            ghosts, [],
            "%d declaration(s) name something no longer seeded: %s. The exemption outlived its "
            "subject, so it now permits a name nobody has examined. [[label-outlived-referent]]"
            % (len(ghosts), ghosts))

    def test_the_bulk_detector_can_actually_see_the_defect_that_shipped(self):
        """BASELINE. Without this, a green law might simply be looking at nothing."""
        fake = dict(("piece %d" % i, "Sep 16, 2026 · 15:28") for i in range(BULK_AT))
        fake["a real find"] = "Aug 24, 2026 · 01:10"
        stamps = Counter(fake.values())
        bulk = {s for s, c in stamps.items() if c >= BULK_AT}
        self.assertIn("Sep 16, 2026 · 15:28", bulk,
                      "the detector cannot see a stamp shared by %d pieces, which is the exact "
                      "shape that shipped" % BULK_AT)
        self.assertNotIn("Aug 24, 2026 · 01:10", bulk,
                         "the detector calls an individually dated find a bulk write — it would "
                         "delete his real finds")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "putting one bulk-stamped Remaining piece back into the shipped seed",
        "file": "bible.html",
        "find": '"Aldur\'s Advance (boots)":',
        "replace": '"Aldur\'s Deception (armor)":"Sep 16, 2026 \\u00b7 15:28","Aldur\'s Advance (boots)":',
        "matches": 1,
    },
    {
        "why": "dropping a declaration leaves a Remaining name seeded with nothing explaining it",
        "file": "tv/bake_seed.py",
        "find": '    "Taebaek\'s Glory (ward)":',
        "replace": '    "Taebaek\'s Glory (ward) RETIRED":',
        "matches": 1,
    },
]
