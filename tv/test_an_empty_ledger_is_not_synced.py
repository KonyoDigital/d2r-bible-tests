# -*- coding: utf-8 -*-
"""HIS CATCH: "SYNCED" SAT DIRECTLY ABOVE "0 / 403 found", AND BOTH CANNOT BE TRUE.

Konyo, 2026-09-07, reading his own fleet card: *"also says synced dean but it says 0/403 so maybe
after he reset it it should read UNSYCNED until he resyncs it again..?"*

What the card said about Dean:

    UNIQUES   SYNCED   "that board declared a ledger of its own, so the owner's seed never landed"
    SETS      SYNCED   (same)        SETS      130 / 135 pieces
    RUNEWORDS SYNCED   (same)        UNIQUES     0 / 403 found     <- the contradiction
                                     RUNEWORDS  96 /  99 made

`SYNCED` is defined at ledger_authority.py:98 as "this ledger's rows were earned on this board".
With zero rows there is nothing that can have been earned. **The label outlived its referent.**
His sets (130) and runewords (96) are non-zero, which is why four provenance answers looked
sufficient for so long — only the empty ledger was incoherent. [[label-outlived-referent]]

=== ⚠⚠ WHY THIS IS NOT `UNKNOWN`, WHICH IS THE DISTINCTION THE WHOLE FIX RESTS ON ===
This module's own doctrine, quoted from its header: "0 IS MEASURED-AND-ZERO, None IS NOBODY LOOKED.
A store that could not be read is None everywhere, never 0." Somebody DID look at Dean's uniques
store and found nothing in it. Collapsing that into UNKNOWN would throw a real measurement away and
say "nobody looked" about a look that happened. UNSYNCED is measured-and-empty.
[[unknown-stays-unknown]] [[zero-needs-a-denominator]]

=== AND THE COMMENT WAS CHANGED, NOT LEFT TO ROT ===
The constants block said "the four provenance answers. There is no fifth". It now says five and
records why. A comment that survives the thing it described is this repo's most repeated defect,
and leaving that sentence in place while adding a fifth value would have been an instance of it.
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

import ledger_authority as LA  # noqa: E402


def _row(have, on_seed=False, **kw):
    t = {"uniques": {"have": have, "total": 403}, "onOwnerSeed": on_seed}
    t.update(kw)
    out = LA.classify_row(t)
    for L in (out.get("ledgers") or []):
        if L.get("ledger") == "uniques":
            return L
    return {}


class AnEmptyLedgerIsNotSynced(unittest.TestCase):

    def test_UNSYNCED_is_a_declared_provenance(self):
        """⚠ A value the module returns but does not declare is one no consumer can be written
        against. The tuple is the contract."""
        self.assertTrue(hasattr(LA, "UNSYNCED"), "UNSYNCED is gone")
        self.assertIn(LA.UNSYNCED, LA.PROVENANCE,
                      "UNSYNCED is returned but not in PROVENANCE, so it is undeclared")

    # ── ⚠⚠ THE LAW ────────────────────────────────────────────────────────────────────────────
    def test_an_empty_declared_ledger_is_UNSYNCED_not_SYNCED(self):
        r = _row(0)
        self.assertEqual(LA.UNSYNCED, r.get("provenance"),
                         "an empty store is still called %r — SYNCED means 'these rows were "
                         "earned on this board' and there are no rows"
                         % r.get("provenance"))
        self.assertIn("EMPTY", str(r.get("why") or ""),
                      "the reason does not say the store is empty, so the card explains nothing")

    def test_a_POPULATED_declared_ledger_is_still_SYNCED(self):
        """The other direction, and it matters: this must not turn into a blanket relabel. His sets
        (130) and runewords (96) were never wrong and must not change."""
        self.assertEqual(LA.SYNCED, _row(130).get("provenance"),
                         "a populated declared-own ledger stopped reading SYNCED")

    # ── ⚠⚠ THE DISTINCTION THE FIX RESTS ON ───────────────────────────────────────────────────
    def test_an_UNREAD_store_is_UNKNOWN_and_never_UNSYNCED(self):
        """`have = None` means nobody looked. Calling that UNSYNCED would publish "this board has
        synced nothing" about a board nobody asked. 0 and None are opposite facts here."""
        r = _row(None)
        self.assertNotEqual(LA.UNSYNCED, r.get("provenance"),
                            "an UNREAD store was labelled UNSYNCED, which is a claim about the "
                            "board rather than about the reading")

    def test_the_seedRows_branch_also_refuses_to_call_an_empty_ledger_SYNCED(self):
        """There are TWO sites that stamp SYNCED. Fixing one and leaving the other is this repo's
        most repeated defect wearing a smaller hat — the bug survives on whichever path was missed."""
        src = io.open(os.path.join(HERE, "ledger_authority.py"), encoding="utf-8").read()
        code = re.sub(r"(?m)^\s*#[^\n]*", "", src)
        self.assertEqual(2, code.count("row[\"provenance\"] = UNSYNCED"),
                         "expected BOTH SYNCED sites to have an empty-store branch; found %d"
                         % code.count("row[\"provenance\"] = UNSYNCED"))

    # ── the surface must be able to render it ────────────────────────────────────────────────
    def test_the_card_has_a_style_for_the_new_value(self):
        """⚠ The fleet card builds its class as 'ftts-' + provenance.toLowerCase(). A value with no
        rule falls through to the default, so the one row that most needs to stand out would render
        exactly like the rows that are fine."""
        ui = io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8").read()
        # ⚠⚠ THE SEED-ROW RULE, NOT THE BARE CLASS NAME — AND v2850 IS WHY.
        # This asserted `.ftts-unsynced` appeared ANYWHERE in the file. That was sufficient while
        # exactly one rule styled the class. v2850 added a SECOND — `.ftt-row.ftt-sync
        # .ftts-unsynced`, for the fleet card's synced/unsynced verdict — and that rule styles a
        # different surface: the verdict row, not the seed row this law is about. From that moment
        # the seed-row rule could have been deleted and this law would still have passed, satisfied
        # by a rule that does not reach the pill it exists to keep visible.
        # PROVEN, not argued: heart2 tampered the seed-row rule away and the gate stayed GREEN —
        # "test_an_empty_ledger_is_not_synced[0] BLIND ← stayed GREEN through its own defeat".
        # A law that names a CLASS is satisfied by any rule mentioning it; a law that names the
        # RULE is satisfied only by that rule. [[label-outlived-referent]] [[the-unjoined-end]]
        self.assertIn(".ftt-seed-rows .ftts-unsynced", ui,
                      "no CSS rule styles .ftts-unsynced INSIDE .ftt-seed-rows — the new "
                      "provenance renders unstyled on the seed rows, whatever other rules "
                      "elsewhere happen to mention the class")

    # ── the comment must not outlive its referent ─────────────────────────────────────────────
    def test_the_constants_block_no_longer_claims_there_are_four(self):
        src = io.open(os.path.join(HERE, "ledger_authority.py"), encoding="utf-8").read()
        head = src[:src.find("PROVENANCE = (")]
        self.assertNotIn("There is no fifth", head,
                         "the block still says 'there is no fifth' beside a fifth value")
        self.assertEqual(5, len(LA.PROVENANCE), "PROVENANCE no longer holds five answers")



# ══ THE EXECUTABLE RED-PROOF ═════════════════════════════════════════════════
# PROPOSED by tv/heart2_candidates.py — derived from this gate's OWN assertions and
# measured against the target file (each anchor occurs exactly once). Review it: the
# question is whether deleting this text is the defect the law exists to catch.
RED_PROOF = [
    {
        "why": 'the law requires this text in control_ui.html, where it occurs exactly once and in no other file the gate names; deleting it must turn the gate red',
        "file": 'control_ui.html',
        # ⚠⚠ NARROWED FROM the bare `.ftts-unsynced`, which v2850 made AMBIGUOUS. The fleet card
        # gained `.ftt-row.ftt-sync .ftts-unsynced` for its synced/unsynced verdict, so the
        # substring occurs TWICE and the gate refused: "the tamper matches 2 time(s), it
        # declares 1". A sabotage that hits two rules deletes more than the law is about, and
        # heart2 is right to refuse it rather than let it pass on the first hit. This anchors
        # the SEED-ROW provenance rule, which is what this law actually guards.
        # [[sabotage-is-usually-the-wrong-one]] [[label-outlived-referent]]
        "find": '.ftt-seed-rows .ftts-unsynced .ftts-pv',
        "replace": '_HEART2_TAMPERED_',
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
