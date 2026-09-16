# -*- coding: utf-8 -*-
"""ON THE SHELF, TOMBSTONE MEANS ONE THING.

Grok Bot's #227 §2, and it is a lie the router itself already documents:

    "TOMBSTONE cannot mean two facts at once — the 21 still on disk vs the 453 that already left."

MEASURED live from /api/river, 2026-09-16:

    lane TOMBSTONE   byStation {"ROUTED": 3, "TOMBSTONE": 0}   closedCount 453
    labels           ROUTED -> TOMBSTONE      TOMBSTONE -> DELETED

Two separate defects sat on top of each other:

 1. THE STRIP PRINTED RAW KEYS while every other shelf surface printed HIS words, so one reel was
    `ROUTED` on the strip and `TOMBSTONE` on its own card. v3176 carved that rule for the card
    badge — "his screen and his logs would then disagree about the name of the same thing" — and
    the strip never got it.
 2. AND SIMPLY APPLYING THE LABELS MAKES IT WORSE. The relabel renders `TOMBSTONE 3` beside
    `DELETED 0` beside `453 closed out`, where the DELETED 0 and the 453 are THE SAME STATION
    reporting two different numbers. That 0 is STRUCTURAL — a closed reel leaves the shelf, so no
    walk of the disk can ever place one there — and printed bare it reads "nothing has been
    deleted" while 453 reels have been. [[zero-needs-a-denominator]]

THE RULE, and the part that keeps it honest: the structural 0 is suppressed ONLY WHEN THE CLOSURE
LEDGER COULD BE READ. When the ledger is unreadable, how many reels have been deleted is genuinely
UNKNOWN, the word must stay sayable, and the labelled 0-chip stays. Suppressing it in both cases
would trade one lie for a quieter one. [[unknown-stays-unknown]]
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

UI = os.path.join(HERE, "control_ui.html")


def _code_only(src):
    src = re.sub(r"/\*.*?\*/", " ", src, flags=re.S)
    return re.sub(r"(?m)^\s*//.*$", " ", src)


def _between(src, start, end):
    i = src.find(start)
    if i < 0:
        return ""
    j = src.find(end, i + len(start))
    return src[i:j] if j > i else ""


class TheRiverHasOneWordPerFact(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with io.open(UI, encoding="utf-8") as fh:
            cls.src = fh.read()
        cls.code = _code_only(cls.src)
        cls.fn = _between(cls.code, "function _shLanesRender(d){", "window._shLanesRender")
        assert cls.fn, "_shLanesRender is gone — this law is reading nothing"
        cls.bits = _between(cls.fn, "var bits = (l.stations || []).map(", "}).join('');")
        assert cls.bits, "the station chip builder is gone"

    def test_the_chips_speak_HIS_words(self):
        self.assertIn("d.labels", self.fn,
                      "the strip no longer reads the label map from /api/river, so it prints raw "
                      "station keys while the card badge prints his words — the same reel then "
                      "has two names on one screen")
        self.assertIn("_LBL[sn]", self.bits,
                      "the chip builder does not apply the label to its own station")

    def test_the_labels_are_NOT_redefined_here(self):
        """[[copy-drift]] — reel_router.HIS_LABELS is the one list, and #227 forbids a second."""
        for w in ("'FRESH'", "'ANALYZE'", "'SEAL'", "'DELETED'"):
            self.assertNotIn(w, self.bits,
                             "a label literal (%s) is hardcoded in the chip builder — that is a "
                             "second roster and it will drift from reel_router" % w)

    def test_the_raw_key_rides_along(self):
        """his screen and his logs must never disagree about the name of one thing."""
        self.assertIn("shr-stkey", self.bits,
                      "the raw station key is no longer shown beside his word, so a log saying "
                      "ROUTED cannot be matched to a chip saying TOMBSTONE")
        self.assertIn("lab !== sn", self.bits,
                      "the raw key is printed even when it equals the label, which is noise")

    # ── the collision itself ──────────────────────────────────────────────────────────────
    def test_the_structural_zero_is_suppressed_when_the_ledger_IS_readable(self):
        self.assertIn("sn === 'TOMBSTONE' && !n && _ledgerRead", self.bits,
                      "the terminal station's structural 0 is rendered beside the ledger's real "
                      "figure — the same station saying two different numbers, which is the "
                      "exact lie this law exists to refuse")

    def test_it_is_suppressed_ONLY_when_the_ledger_is_readable(self):
        """the honesty clause. Suppressing it unconditionally trades one lie for a quieter one."""
        self.assertIn("_ledgerRead = (l.closedCount === 0 || l.closedCount)", self.fn,
                      "nothing distinguishes a ledger that was READ from one that could not be — "
                      "and `0` and `null` are different answers about how many reels were deleted")
        self.assertNotIn("sn === 'TOMBSTONE' && !n)", self.bits,
                         "the structural 0 is suppressed even when the ledger is UNREADABLE, so "
                         "the word DELETED disappears exactly when the count is unknown")

    def test_the_word_DELETED_actually_reaches_a_screen(self):
        """[[plumbing-with-no-tap]] — before this, all 20 occurrences of DELETED in this file were
        comment prose. A vocabulary nobody renders is not a vocabulary."""
        rendered = [m for m in re.finditer(r"deleted", self.code, re.I)]
        self.assertTrue(rendered,
                        "the word DELETED appears nowhere outside comments, so the 453 that left "
                        "the disk have no name on any surface")

    def test_the_pinned_reason_survives(self):
        """test_the_shelf_shows_the_four_lanes pins this phrase; a zero with its reason removed is
        the defect the note was written for."""
        self.assertIn("leaves the shelf", self.fn,
                      "the structural zero lost the sentence explaining why it is zero")

    def test_the_note_names_BOTH_stations(self):
        """the paragraph must not become the collision it explains."""
        self.assertIn("(key TOMBSTONE)", self.fn,
                      "the note says DELETED without naming the raw key, so it cannot be matched "
                      "to the router's own vocabulary")
        self.assertIn("(key ROUTED)", self.fn,
                      "the note says TOMBSTONE without saying WHICH TOMBSTONE — the chip one inch "
                      "away now uses that word for a different station")

    def test_lane_NAMES_are_left_alone(self):
        """#227: do not relabel lane names. `test_the_shelf_shows_the_four_lanes` asserts INTAKE
        before TOMBSTONE in lane order, and relabelling INTAKE to FRESH breaks it."""
        self.assertIn("esc(l.name)", self.fn,
                      "the lane name is being relabelled; lanes are not stations and the lane "
                      "order law reads their raw names")


RED_PROOF = [
    ("control_ui.html", "if (sn === 'TOMBSTONE' && !n && _ledgerRead) return '';",
     "if (sn === 'TOMBSTONE' && !n && false) return '';",
     "test_the_structural_zero_is_suppressed_when_the_ledger_IS_readable"),
    ("control_ui.html", "var lab = (_LBL && _LBL[sn]) || sn;", "var lab = sn;",
     "test_the_chips_speak_HIS_words"),
    ("control_ui.html", "+ (lab !== sn ? '<i class=\"shr-stkey\">' + esc(sn) + '</i>' : '')",
     "+ ''", "test_the_raw_key_rides_along"),
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
