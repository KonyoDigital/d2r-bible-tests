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
        self.assertIn(".sh-daygroup.sh-rivermouth .shg-lab::after { content: none; }", UI,
                      "the ' · never reached' suffix is not suppressed at the mouth, so the header "
                      "asserts the opposite of the number beside it")
        self.assertIn(".sh-daygroup.sh-rivermouth { opacity: 1; }", UI,
                      "the mouth is still dimmed like an empty station")

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
        self.assertIn("MB reclaimed", CODE, "the reclaimed figure is not shown in code")
        self.assertIn("undated", CODE,
                      "undated rows are not surfaced — a timeline that omits them silently is the "
                      "defect this view exists to prevent")

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
