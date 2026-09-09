# -*- coding: utf-8 -*-
"""THE SHELF'S TOMBSTONE SECTION SAID "never reached" OVER 410 COMPLETED JOURNEYS.

Konyo asked for THE SHELF drawn as the river, "down the river ending in extraction and then
TOMBSTONE ... i can literaly see REEL SESSIONS timestamped from first in to first out FIFO and
eventually pruned and deleted in tombstone".

The river view already printed every station including the empty ones — deliberately, because "a
section that vanishes when empty hides the finding". But it counted CARDS, and at TOMBSTONE the
card count can only ever be zero: **a closed-out reel LEAVES THE DISK.** It stops being a card and
becomes a row in the retention ledger.

MEASURED: 410 tombstoned reels, 5,768.1 MB reclaimed, and the overlap with the 40 living reels is
EXACTLY ZERO. I read `counts.TOMBSTONE: 0` as "nothing ever finished" and told him so. It was
wrong, and the shelf would have told him the same thing in bigger type.

⚠⚠ AND THE CSS WOULD HAVE PRINTED THE CONTRADICTION IN ONE LINE. `.sh-riverempty .shg-lab::after`
appends " · never reached" to any station with no cards. With the mouth wired in, the header read:

        TOMBSTONE · never reached · 410 closed out

the false claim and its own refutation, side by side. So the mouth suppresses that ::after and is
not dimmed like an empty station — a section carrying a real terminus is not empty.
[[label-outlived-referent]] [[zero-needs-a-denominator]]

⚠ AND THE COUNT SAYS WHERE IT CAME FROM. The card count is the ROUTER's answer; the closed-out
count is the LEDGER's. Two numbers from two stores under one heading, unlabelled, is exactly the
confusion this whole view exists to end.
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

UI = io.open(os.path.join(HERE, "control_ui.html"), encoding="utf-8").read()


def _code_only(src):
    """Blank out /* */ and // comments.

    ⚠ WRITTEN IN FROM THE START THIS TIME. Four laws this session were fooled by the prose
    explaining the very rule they enforce — a docstring saying "must never call X" matching a
    grep for X. A guard that greps prose grades prose. [[source-reading-guard]]
    """
    src = re.sub(r"/\*.*?\*/", lambda m: " " * len(m.group(0)), src, flags=re.S)
    return re.sub(r"(?m)//[^\n]*", lambda m: " " * len(m.group(0)), src)


CODE = _code_only(UI)


class TheShelfShowsTheMouth(unittest.TestCase):

    def test_the_guard_can_find_the_river_section_builder(self):
        """⚠ A law that cannot find its subject passes having examined nothing."""
        self.assertIn("order.slice().reverse().forEach", CODE,
                      "the river section builder is gone or renamed — fix this guard first")

    # ── the mouth reaches the view at all ─────────────────────────────────────────────────────
    def test_the_mouth_is_CARRIED_off_the_river_payload(self):
        self.assertIn("SHELF_MOUTH = d.mouth || null;", CODE,
                      "the shelf never reads `mouth` off /api/river, so the terminus cannot render")

    def test_the_mouth_starts_NULL_and_null_is_not_zero(self):
        """`null` = the river has not answered yet. Rendering that as "0 closed out" would repeat
        the exact mistake this whole gate exists for. [[unknown-stays-unknown]]"""
        self.assertIn("var SHELF_MOUTH = null;", CODE, "SHELF_MOUTH no longer starts null")
        self.assertIn("SHELF_MOUTH === null", CODE,
                      "nothing distinguishes 'not read yet' from an empty ledger")
        self.assertIn("ledger not read yet", UI,
                      "the not-yet-read state has no wording, so it renders as silence")

    def test_an_UNREADABLE_ledger_says_why_rather_than_showing_none(self):
        self.assertIn("SHELF_MOUTH.ok === false", CODE,
                      "a ledger that could not be read is not handled, so it renders as 0 finished")

    # ── ⚠⚠ THE CONTRADICTION THAT WOULD HAVE SHIPPED ──────────────────────────────────────────
    def test_the_mouth_suppresses_never_reached(self):
        """Without this the header prints "TOMBSTONE · never reached · 410 closed out"."""
        self.assertIn(".sh-daygroup.sh-rivermouth .shg-n::after { content: none; }", UI,
                      "the ' · never reached' suffix is not suppressed at the mouth, so the header "
                      "asserts the opposite of the number beside it")
        self.assertIn(".sh-daygroup.sh-rivermouth { opacity: 1; }", UI,
                      "the mouth is still dimmed like an empty station")

    def test_never_reached_sits_AFTER_the_count_not_between_name_and_number(self):
        """⚠ FOUND BY A COLD EYE, NOT BY GEOMETRY. On `.shg-lab::after` the row rendered
        "INTAKE ·never reached 0 REELS" — a status message wedged between a station's name and its
        number. Grok, shown the sections with no idea what they were: "the repeated 'never reached
        0 REELS' strings look like placeholder/debug text that was never replaced". Nothing
        overflowed, nothing clipped; it simply read as unfinished."""
        self.assertIn(".sh-daygroup.sh-riverempty .shg-n::after", UI,
                      "the 'never reached' state is not on the count — if it is back on the label "
                      "it renders between the station name and its number and reads as debris")
        self.assertNotIn(".sh-daygroup.sh-riverempty .shg-lab::after", UI,
                         "the label still carries the state suffix")

    def test_the_mouth_class_is_only_applied_when_the_LEDGER_HAS_ROWS(self):
        """⚠ It must not fire on an unread or empty ledger — that would suppress 'never reached'
        for a station that genuinely has not been reached, which is the other direction of the same
        lie."""
        self.assertIn("SHELF_MOUTH.n === 'number' && SHELF_MOUTH.n > 0", CODE,
                      "the mouth styling is applied without proving the ledger holds rows")
        self.assertIn("_mouthHasRows ? ' sh-rivermouth' : ''", CODE,
                      "the class is computed but never applied")

    # ── the two numbers must be distinguishable ───────────────────────────────────────────────
    def test_the_closed_out_count_is_LABELLED_not_merged_into_the_card_count(self):
        """The card count is the ROUTER's answer; the closed-out count is the LEDGER's. Merging
        them would make a station with no cards indistinguishable from a terminus with 410."""
        # ⚠ AGAINST `CODE`, NOT `UI` — this law FIRST asserted against the raw file and passed a
        # sabotage that deleted the label, because the words "closed out" also appear in the
        # comment ABOVE the code explaining the label. Fifth instance of that shape today, in the
        # one gate that already had a comment-stripper sitting unused. [[source-reading-guard]]
        self.assertIn("' closed out'", CODE,
                      "the ledger figure has no label IN CODE, so it reads as more reels on the "
                      "shelf")
        # ⚠ THE WORDING CHANGED AFTER THIS LAW WAS WRITTEN AND I DID NOT RE-RUN IT. The law said
        # "MB reclaimed"; a later compaction to GB made it "freed", and v2758 shipped with this
        # gate RED — the pre-push runs three of the thirty gate files, so nothing caught it.
        # Pinned on the SHAPE now (a size and the word freed) rather than one phrasing, so a units
        # change does not falsify the law again. [[regression-guard]]
        self.assertIn("' freed'", CODE, "the freed-size figure has no label in code")
        self.assertIn("' GB'", CODE, "the size is not compacted to GB, so a 4-digit MB figure "
                                     "returns to the header")
        self.assertIn("' MB'", CODE, "the sub-1GB case lost its unit")
        self.assertIn("undated", CODE,
                      "undated rows are not surfaced — a timeline that omits them silently is the "
                      "defect this view exists to prevent")

    def test_the_terminus_does_NOT_open_with_a_zero_it_knows_is_meaningless(self):
        """★ v2759 — FOUND BY THE SECOND EYE ON PIXELS, NOT BY ANY GATE HERE.

        The row rendered `TOMBSTONE 0 REELS · 410 CLOSED OUT · 5.6 GB FREED`. grok-4-1-fast-
        reasoning, shown only the crop and told nothing about the intent, read it cold:
        "The user reads 'TOMBSTONE 0 REELS' first because that phrase uses the same structure and
        weight as every other station row above it. The immediate conclusion is 'nothing reached
        this stage', exactly the opposite of the intended message."

        ⚠ THE CODE ALREADY KNEW. The comment above the class line says `cs.length` "can only ever
        be 0" at this station — and the header printed it first regardless. Every gate here was
        green: they all checked that the closed-out figure was PRESENT and LABELLED, and not one
        asked what the eye meets first. A number can be correct, labelled, measured and still
        say the opposite of the truth by where it sits. [[label-outlived-referent]]

        ⚠ SUPPRESSED, NOT DELETED — and that is the half the second eye got wrong. It proposed
        removing the count. MEASURED against reel_router first: TOMBSTONE is terminal ("nothing —
        it is released, and the stamp is its record") and holds 0 of 40 living reels today, but a
        reel stamped tombstone whose file is not yet gone WOULD be a real card, and a row that can
        never show one hides the single case worth seeing. So the zero goes only while the ledger
        has journeys to print in its place.
        """
        self.assertIn("_mouthSpeaks", CODE,
                      "nothing decides whether the ledger has something to say in the count's "
                      "place, so the suppression cannot be conditional")
        self.assertIn("if (!(_mouthSpeaks && cs.length === 0)){", CODE,
                      "the card count is not guarded on a SPEAKING mouth over ZERO cards. Either "
                      "the zero is back in front of the 410, or the count was dropped outright — "
                      "which would hide a tombstoned-but-not-yet-deleted reel.")
        self.assertNotIn("'<span class=\"shg-n\">' + cs.length + ' reel'", CODE,
                         "the header builds the count unconditionally again, so TOMBSTONE opens "
                         "with a 0 that the code's own comment calls meaningless")
        # ⚠ the separator moved to the JOIN, so a mouthBit still carrying its own leading '·'
        # would render a doubled separator the moment the count IS suppressed.
        self.assertNotIn("mouthBit = ' \\u00b7 ", CODE,
                         "a mouthBit still carries a leading separator; with the count suppressed "
                         "the row renders 'TOMBSTONE  \u00b7 410 closed out'")
        self.assertIn("_bits.join(' \\u00b7 ')", CODE,
                      "the header no longer joins its parts, so separator placement is back to "
                      "being hardcoded per fragment")

    def test_it_is_scoped_to_TOMBSTONE_only(self):
        """⚠ COUNTS BOTH SITES. This first asserted the string was present ANYWHERE, and passed a
        sabotage that unscoped one of the two checks — the guard survived on its twin while the
        defect shipped. Two independent places decide "is this the mouth" (the styling class and
        the header text); either one unscoped lets another station claim the terminus."""
        n = CODE.count("String(st).toUpperCase() === 'TOMBSTONE'")
        self.assertEqual(2, n,
                         "expected BOTH mouth checks (the styling class and the header text) to be "
                         "scoped to TOMBSTONE; found %d. One unscoped check is enough for another "
                         "station to render as the terminus." % n)



# ══ THE EXECUTABLE RED-PROOF ═════════════════════════════════════════════════
# PROPOSED by tv/heart2_candidates.py — derived from this gate's OWN assertions and
# measured against the target file (each anchor occurs exactly once). Review it: the
# question is whether deleting this text is the defect the law exists to catch.
RED_PROOF = [
    {
        "why": 'the law requires this text in control_ui.html, where it occurs exactly once and in no other file the gate names; deleting it must turn the gate red',
        "file": 'control_ui.html',
        "find": 'order.slice().reverse().forEach',
        "replace": '_HEART2_TAMPERED_',
        "matches": 1,
    },
    {
        "why": 'the law requires this text in control_ui.html, where it occurs exactly once and in no other file the gate names; deleting it must turn the gate red',
        "file": 'control_ui.html',
        "find": 'SHELF_MOUTH = d.mouth || null;',
        "replace": '_HEART2_TAMPERED_',
        "matches": 1,
    },
    {
        "why": 'the law requires this text in control_ui.html, where it occurs exactly once and in no other file the gate names; deleting it must turn the gate red',
        "file": 'control_ui.html',
        "find": 'var SHELF_MOUTH = null;',
        "replace": '_HEART2_TAMPERED_',
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
