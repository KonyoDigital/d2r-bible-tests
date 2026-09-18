# -*- coding: utf-8 -*-
"""v3321 — "WAITING ON YOU" CARRIES ONLY WHAT IS ACTUALLY HIS.

His #35 ruling: **WAITING ON YOU means action needed FROM HIM RIGHT NOW.** MEASURED on his live
console 2026-09-18, that panel carried EIGHT rows and `owner_of()` answered "you" for all eight,
while exactly ONE was his. He read it and asked: *"this is the missing on me?"*

    engines corroborate   two engines disagree, "not knowable from the pair alone"   -> mine
    console UI faults     "the console healed itself ... It recovered"               -> mine
    ledger provenance     carries its own named fix                                  -> mine
    footage has a reel    1 frame in no reel; orphan_fold.py shows the plan          -> mine
    names banked          names READ, none banked; "no paid read is owed here"       -> mine
    stage shows the dom   "a stale composite, which every guard reports as success"  -> mine
    river joints          by-design TODAY, genuinely his the day something IS
                          safe to delete — a CONDITIONAL, deliberately left out      -> open
    shadow gate           "that list ... is yours to read"                           -> HIS

A column that cries for him on seven rows he cannot act on is the same defect as a gate that is
always red: he stops reading it, and the one row that IS his goes with it.

⚠⚠ THE HALF THAT MATTERS MOST IS THE BASELINE. The cheap way to make this panel quiet is to call
everything mine, and that would be far worse than the noise — it would empty the one column he
relies on while looking like a fix. So this law pins BOTH directions: the six move, and a row that
is genuinely his STILL reaches him.

⚠ CLASSIFYING IS NOT MUTING. MINE and BY_DESIGN rows still render, at their real state and colour;
only the name on the row changes. A row removed is a row nobody can reopen — which is why every
key here must name a check that actually exists, or the entry is dead config silently classifying
nothing. [[regression-guard]] [[label-outlived-referent]]
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import console_doctor as cd  # noqa: E402

#: Genuinely his, and the law exists as much to protect this as to move the others.
HIS = "shadow gate"


class TestWaitingOnYouMeansWaitingOnHim(unittest.TestCase):

    def setUp(self):
        self.names = set(n for n, _fn in cd.CHECKS)
        self.assertGreater(
            len(self.names), 20,
            "only %d check(s) are registered — this law measured almost nothing, so a PASS is "
            "UNMEASURED. [[zero-needs-a-denominator]]" % len(self.names))

    def test_every_classified_row_names_a_check_that_exists(self):
        """Dead config classifies nothing and reads exactly like a working exemption."""
        ghosts = sorted(k for k in (set(cd.MINE) | set(cd.BY_DESIGN)) if k not in self.names)
        self.assertEqual(
            ghosts, [],
            "%d classified row(s) name a check that is not registered: %s\n"
            "A typo here is invisible: the row keeps billing him and the entry looks like it is "
            "handling it. Names must match cd.CHECKS exactly." % (len(ghosts), ghosts))

    def test_a_row_that_is_genuinely_his_still_reaches_him(self):
        """⚠ THE BASELINE. Without this, 'classify everything as mine' passes every other check."""
        self.assertIn(HIS, self.names,
                      "%r is not a registered check, so this baseline proves nothing about the "
                      "column it is meant to protect." % HIS)
        self.assertEqual(
            cd.owner_of(HIS), "you",
            "%r no longer reaches him. Its own sentence ends 'that list is the argument for or "
            "against switching, and it is yours to read' — it is a judgement only he can make. "
            "Quieting the panel by taking his rows away is worse than the noise it removes." % HIS)
        self.assertNotIn(HIS, cd.MINE, "%r was classified as mine; it is a ruling, not a defect" % HIS)
        self.assertNotIn(HIS, cd.BY_DESIGN, "%r was classified by-design; it is a live question" % HIS)

    def test_the_six_measured_rows_no_longer_bill_him(self):
        """The rows he was shown on 2026-09-18, each with a reason he cannot act on."""
        moved = ("engines corroborate", "console UI faults", "ledger provenance",
                 "footage has a reel", "names banked", "stage shows the dom")
        wrong = sorted(n for n in moved if cd.owner_of(n) != "me")
        self.assertEqual(
            wrong, [],
            "%d row(s) still bill him for my work: %s. Each was measured on his console under a "
            "heading his #35 ruling defines as 'action needed FROM HIM RIGHT NOW'."
            % (len(wrong), wrong))

    def test_every_classification_carries_a_reason(self):
        """An unexplained exemption is how the list grows into a mute button."""
        empty = sorted(k for k, why in list(cd.MINE.items()) + list(cd.BY_DESIGN.items())
                       if not str(why or "").strip())
        self.assertEqual(
            empty, [],
            "%d classification(s) carry no reason: %s. A row leaves his column only because "
            "someone can say why." % (len(empty), empty))

    def test_classifying_is_not_removing(self):
        """A classified row must still be a running check, or it stopped being watched."""
        gone = sorted(k for k in set(cd.MINE) if k not in self.names)
        self.assertEqual(
            gone, [],
            "%d row(s) are classified as mine but no longer run: %s. Classification changes whose "
            "name is on a row, never whether it is measured." % (len(gone), gone))


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "calling everything mine empties the one column he relies on",
        "file": "tv/console_doctor.py",
        "find": '    return "me" if name in MINE else "you"',
        "replace": '    return "me"',
        "matches": 1,
    },
    {
        "why": "a classified row naming a check that does not exist silently classifies nothing",
        "file": "tv/console_doctor.py",
        "find": '    "engines corroborate":\n        "#81 —',
        "replace": '    "engines corroborate TYPO":\n        "#81 —',
        "matches": 1,
    },
]
