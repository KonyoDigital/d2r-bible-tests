# -*- coding: utf-8 -*-
"""v3313 — A SEED IS COMPARED ONLY TO A FIGURE THAT COUNTS THE SAME POPULATION.

`uniques seed` carried a permanent `+N behind the live figure` and nothing could close it. The
subtraction was `chronFound - len(_GRAIL_SEED)`, and those two count different things:

    len(_GRAIL_SEED)   a list of NAMES the boot floor would write into d2r_foundLog
    chronFound         `funiScan().found` — a walk of the ROSTER, asking `_ownedHas` of each row,
                       which resolves a store name to its canonical form before matching

So the seed legitimately carries alias spellings with no row of their own (the six
`Latent <sunder>` forms are dropped by `_uniItems`; `Harlequin Crest (Shako)` resolves onto the
row spelled `Harlequin Crest`), and his store legitimately holds rows the seed never listed. The
two can be level only by coincidence.

⚠⚠ THIS ROW GAVE ME AN INSTRUCTION AND I FOLLOWED IT. On 2026-09-18 it read `+63 behind`, so 67
names were written into `_GRAIL_SEED`. It then read `-3 behind`. Measured afterwards on his live
board: seed 312 names, `chronFound` 309, and **0 of those 312 names are absent from his store** —
there was never any missing work. A permanently-red row is not merely ignored; it is obeyed.

⚠ THE FACT WAS ALREADY RECORDED AND TWO SITES NEVER ASKED. Every ledger declares
`usesStoreLength`, and `canonical_figure` already refuses this exact comparison on that field —
*"NOT A COMPARISON, AND SAYING SO MATTERS ... UNKNOWN by non-applicability, never a false red"*.
`_stale()` and the FROZEN row builder both subtracted anyway. [[the-unjoined-end]] [[copy-drift]]

⚠ AND THE REAL FINDING MUST SURVIVE. `sets` and `runewords` ARE store lengths, so their drift is a
true subtraction. Dean's runewords read 94 against a seed of 99 — five seeded rows genuinely
missing from his store. A fix that exempted those would be the cure killing the patient, so that
case is pinned here as a BASELINE rather than left to inference. [[regression-guard]]

THREE STATES, AND COLLAPSING ANY TWO IS THE DEFECT:
    comparable True  + drift int    the figures count one population; the distance is real
    comparable False + drift None   different populations — no distance EXISTS to report
    comparable True  + drift None   they would compare, but nobody published a live figure
[[unknown-stays-unknown]] [[zero-needs-a-denominator]]
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

# Its docstrings and failure messages carry non-ASCII, and a unittest failure PRINTS them. On a
# cp1255 console that crash happens while REPORTING, so a clean tree exits non-zero for a reason
# that has nothing to do with the law. Caught by test_control's encoding-safety gate.
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import ledger_authority as LA  # noqa: E402

#: A fixture ceiling. The real one is derived from the live pipeline; this law is about which rows
#: are GRADED, not about where the threshold sits, so a constant here cannot make it lie.
CEIL = {"ceilingMs": 480000.0, "staleMs": 1440000.0,
        "parts": {"beaconPeriodS": 240.0, "tallyTtlS": 180.0, "fleetCacheS": 60.0, "multiple": 3.0},
        "how": "a FIXTURE ceiling — this law grades which rows are compared, not the threshold"}


def _spec(name):
    for s in LA.LEDGERS:
        if s["name"] == name:
            return s
    raise AssertionError("no ledger named %r — the roster this law reads has moved" % name)


class TestASeedIsComparedOnlyToItsOwnPopulation(unittest.TestCase):

    def test_a_roster_walk_is_never_subtracted_from_a_name_list(self):
        """BEHAVIOURAL. Every ledger that declares it is not a store length refuses the distance."""
        refused = 0
        for spec in LA.LEDGERS:
            if spec.get("usesStoreLength"):
                continue
            refused += 1
            got = LA.seed_drift(spec, 312, 309)
            self.assertIs(
                got["comparable"], False,
                "%s declares usesStoreLength=False — its live figure is a walk of the roster, not "
                "the length of %s — yet seed_drift reported comparable=%r. Subtracting a "
                "roster-ROW count from a seed NAME count is what made this row permanently red, "
                "and a permanently red row gets obeyed."
                % (spec["name"], spec.get("store"), got["comparable"]))
            self.assertIsNone(
                got["drift"],
                "%s reported a drift of %r. There is no distance between two different "
                "populations; publishing one invites an action that cannot close it."
                % (spec["name"], got["drift"]))
            self.assertIsNone(
                got["stale"],
                "%s reported stale=%r. A comparison that was never valid is not a figure that has "
                "gone out of date." % (spec["name"], got["stale"]))

        # A zero needs a denominator: if no ledger is of this kind the assertions above ran zero
        # times and this test's PASS is not evidence about anything.
        self.assertGreaterEqual(
            refused, 1,
            "no ledger declares usesStoreLength=False, so this law graded NOTHING and its pass is "
            "meaningless. [[zero-needs-a-denominator]]")

    def test_a_store_length_ledger_keeps_its_real_drift(self):
        """BASELINE, and the one that must never be 'fixed'. Dean's runewords: 94 held, 99 seeded."""
        got = LA.seed_drift(_spec("runewords"), 99, 94)
        self.assertIs(
            got["comparable"], True,
            "runewords publishes len(d2r_rwMade) — the same population its seed lists — so the "
            "subtraction is valid and must stay. comparable came back %r." % (got["comparable"],))
        self.assertEqual(
            got["drift"], -5,
            "Dean's runewords read 94 against a seed of 99: five seeded rows are MISSING from his "
            "store, which is a real fact about his board. This law reported drift=%r instead. "
            "Exempting the valid comparisons along with the invalid one would be the cure killing "
            "the patient." % (got["drift"],))
        self.assertIs(
            got["stale"], True,
            "a five-row gap on a valid comparison must still read stale; it came back %r."
            % (got["stale"],))

    def test_comparability_is_decided_before_the_live_figure_is_looked_at(self):
        """A dark board must not make the exemption disappear."""
        got = LA.seed_drift(_spec("uniques"), 312, None)
        self.assertIs(
            got["comparable"], False,
            "with no live figure published, uniques reported comparable=%r. Comparability is a "
            "property of the LEDGER, not of the reading — deciding it from the live value means a "
            "quiet board reads as 'comparable, merely unmeasured' and the exemption vanishes "
            "exactly when nothing can check it." % (got["comparable"],))

        # ...and the third state stays distinct: a ledger that WOULD compare, with nothing to
        # compare against, is UNKNOWN — not exempt, and not zero.
        sets = LA.seed_drift(_spec("sets"), 133, None)
        self.assertIs(
            sets["comparable"], True,
            "sets is a store length and must stay comparable even when no figure was published; "
            "it came back %r. Collapsing 'nobody asked' into 'not applicable' loses the finding "
            "that a board went quiet." % (sets["comparable"],))
        self.assertIsNone(
            sets["drift"],
            "sets reported drift=%r against a live figure of None. A missing reading is UNKNOWN, "
            "never a measured zero." % (sets["drift"],))

    def test_the_seed_stale_row_publishes_no_distance_it_cannot_justify(self):
        """`behind` is what the console prints. It must be absent, not zero, when invalid."""
        uni = LA._stale(312, 309, [], _spec("uniques"))
        self.assertIsNone(
            uni["behind"],
            "the uniques seedStale row still carries behind=%r. That is the exact number that "
            "read '-3 behind the live figure' and sent 67 names into the seed." % (uni["behind"],))
        self.assertIs(
            uni["comparable"], False,
            "the row does not carry comparable=False, so a reader taking `behind` has no way to "
            "know the subtraction was declined. The caveat must ride ON the row.")
        self.assertTrue(
            uni.get("comparableWhy"),
            "the row gives no reason for declining. A refusal without a reason reads as a bug.")

        # BASELINE — the same helper still publishes a distance where one exists.
        rw = LA._stale(99, 94, [], _spec("runewords"))
        self.assertEqual(
            rw["behind"], -5,
            "the runewords seedStale row lost its real distance (behind=%r). This test can only "
            "tell the two apart if the valid case still reports." % (rw["behind"],))

    def test_a_peer_board_is_not_split_into_inherited_and_earned_by_an_invalid_subtraction(self):
        """THE THIRD COPY. `beyondSeed` is `have - seed_n` too, and the sweep found it.

        It hid until the seed grew: a peer holding 249 against a seed of 245 read "about 4 were
        earned there"; against a seed of 312 the same board reads "63 seeded row(s) are MISSING
        from its store". Both are claims about ROWS computed from a count of NAMES.
        """
        v = LA.classify_row({"ok": True, "onOwnerSeed": True,
                             "uniques": {"have": 249, "total": 403}})
        row = [r for r in v["ledgers"] if r["ledger"] == "uniques"][0]

        self.assertIsNone(
            row["beyondSeed"],
            "a peer board's uniques figure was split into inherited and earned as %r. That number "
            "is a roster-row count minus a seed name count, and it changes whenever the seed is "
            "edited without anything happening on that board." % (row["beyondSeed"],))
        self.assertEqual(
            row["provenance"], LA.SEEDED,
            "the board still runs on the owner's seed — declining the SPLIT must not change the "
            "PROVENANCE, or a real fact is lost along with the invalid one.")
        self.assertIn(
            "UNKNOWN", row["why"],
            "the row does not say the split is unknown, so a reader sees a missing number rather "
            "than a declined one. Said: %s" % row["why"])
        self.assertNotIn(
            "MISSING from its store", row["why"],
            "the row still accuses that board of missing seeded rows on arithmetic that cannot "
            "support it. Said: %s" % row["why"])

        # BASELINE — the split still happens where the subtraction is real.
        v2 = LA.classify_row({"ok": True, "onOwnerSeed": True,
                              "runewords": {"have": 120, "total": 135}})
        rw = [r for r in v2["ledgers"] if r["ledger"] == "runewords"][0]
        self.assertIsInstance(
            rw["beyondSeed"], int,
            "runewords publishes len(d2r_rwMade), so inherited-vs-earned IS derivable there and "
            "must keep being derived; it came back %r. Without this the test cannot tell a "
            "declined split from a deleted feature." % (rw["beyondSeed"],))

    def test_the_doctor_neither_bills_him_for_it_nor_counts_it_as_current(self):
        """The screen half. An exemption that is invisible is an exemption that grows."""
        import console_doctor as CD

        rows = [
            {"name": "uniques seed", "kind": LA.FROZEN, "value": 312, "drift": None,
             "stale": None, "comparable": False,
             "comparableWhy": "uniques does not publish len(d2r_foundLog) as its figure",
             "ageKnown": False, "ageMs": None, "machineOff": False},
            {"name": "uniques live", "kind": LA.LIVE, "value": 309, "drift": None,
             "stale": False, "ageKnown": True, "ageMs": 1000, "machineOff": False},
        ]

        def _run(rs):
            # Patch the NAMES THE CODE CALLS. `_board_read`/`_get` gate the early return, and the
            # check does `import ledger_authority as LA` inside itself, so the module attribute is
            # the one it reaches. Patching anything else here would go inert and read as a pass.
            _br, _g, _st = CD._board_read, CD._get, LA.staleness
            try:
                CD._board_read = lambda *a, **k: {"ok": True}
                CD._get = lambda *a, **k: {"ok": True}
                LA.staleness = lambda *a, **k: {"rows": rs, "ceiling": CEIL}
                return CD._check_no_ledger_FIGURE_has_gone_stale_unnoticed()
            finally:
                CD._board_read, CD._get, LA.staleness = _br, _g, _st

        state, say = _run(rows)

        # ⚠ ANCHOR ON THE FAULT SENTENCE, NOT THE PHRASE. A bare `assertNotIn("out of date")`
        # trips on the EXEMPTION's own wording — "not comparable by construction rather than out
        # of date" — so the law would fail on the very text proving it works. That is this repo's
        # most-repeated guard defect and it caught me writing this line. [[source-reading-guard]]
        self.assertEqual(
            state, CD.OK,
            "the doctor returned %r for a row that is exempt by construction and a healthy live "
            "figure. Nothing here is out of date and nothing is undatable." % (state,))
        self.assertNotIn(
            "ledger figure(s) are out of date", say,
            "the doctor still bills him for the non-comparable figure:\n  %s" % say)
        self.assertIn(
            "not comparable by construction", say,
            "the exemption is not named on the row. An exemption nobody can see is one that grows "
            "silently — the same discipline as `_BY_DESIGN_STATIONS` on the river row. Said:\n  %s"
            % say)
        self.assertIn(
            "1 of 2", say,
            "the row counts the exempt figure among the current ones. 'N of M are current' must "
            "exclude a figure that was never graded, or a clean verdict quietly covers an "
            "unexamined row. Said:\n  %s" % say)

        # ⚠ BASELINE — without it, a check that returns OK for EVERY input would pass the three
        # assertions above while measuring nothing. Flip the one field and the fault must appear.
        hot = [dict(rows[0], comparable=True, stale=True, drift=-3), rows[1]]
        state2, say2 = _run(hot)
        self.assertEqual(
            state2, CD.MISSING,
            "with the same row marked comparable and drifting, the doctor returned %r rather than "
            "MISSING — so this case cannot tell a graded row from an exempt one and proves "
            "nothing about either." % (state2,))
        self.assertIn(
            "ledger figure(s) are out of date", say2,
            "a genuinely drifting comparable figure no longer reports as out of date. The "
            "exemption has swallowed the fault it was carved beside. Said:\n  %s" % say2)


    def test_a_row_excluded_for_two_reasons_is_subtracted_once(self):
        """v3317, FOUND BY THE SECOND EYE ON v3314. Two counts, one row, subtracted twice.

        `len(rows) - len(off) - len(nocmp)` double-subtracts a row that is BOTH switched-off and
        non-comparable. Measured on the live walk the day it was found: rows=10, off=1, nocmp=1,
        BOTH=0 — so the printed figure was correct THAT DAY, by accident. `machineOff` is stamped
        in the fleet-beacon loop and `comparable` in the FROZEN seed loop, and nothing makes those
        populations disjoint. This case builds the overlap the live data does not happen to have,
        which is the only way a latent divergence can be seen RED. [[regression-guard]]
        """
        import console_doctor as CD

        rows = [
            {"name": "peer seed", "kind": LA.FROZEN, "value": 1, "drift": None, "stale": None,
             "comparable": False, "comparableWhy": "a roster walk, not a store length",
             "machineOff": True, "why": "that laptop is switched off",
             "ageKnown": False, "ageMs": None},
            {"name": "local live", "kind": LA.LIVE, "value": 2, "drift": None, "stale": False,
             "ageKnown": True, "ageMs": 1000, "machineOff": False},
        ]

        _br, _g, _st = CD._board_read, CD._get, LA.staleness
        try:
            CD._board_read = lambda *a, **k: {"ok": True}
            CD._get = lambda *a, **k: {"ok": True}
            LA.staleness = lambda *a, **k: {"rows": rows, "ceiling": CEIL}
            _state, say = CD._check_no_ledger_FIGURE_has_gone_stale_unnoticed()
        finally:
            CD._board_read, CD._get, LA.staleness = _br, _g, _st

        self.assertIn(
            "1 of 2 ledger figure(s) are current", say,
            "one row is excluded for TWO reasons and was subtracted twice, so the count of "
            "current figures is under-reported — and on a smaller ledger it would go negative. "
            "Said:\n  %s" % say)
        self.assertNotIn(
            "0 of 2 ledger figure(s) are current", say,
            "the double-subtraction is still there: 2 rows minus one row counted twice is 0. "
            "Said:\n  %s" % say)


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "ignoring usesStoreLength restores the subtraction that made the row permanently red",
        "file": "tv/ledger_authority.py",
        "find": '    if not spec.get("usesStoreLength"):\n        out["comparable"] = False',
        "replace": '    if False:\n        out["comparable"] = False',
        "matches": 1,
    },
    {
        "why": "a `behind` computed regardless of comparability is the number that sent 67 names in",
        "file": "tv/ledger_authority.py",
        "find": '        "behind": (None if _comparable is False\n                   else ((have - seed_n) if isinstance(have, int) else None)),',
        "replace": '        "behind": ((have - seed_n) if isinstance(have, int) else None),',
        "matches": 1,
    },
    {
        "why": "splitting a peer board on the invalid subtraction accuses it of missing rows",
        "file": "tv/ledger_authority.py",
        "find": '        if on_seed is True and _cmp["comparable"] is False:',
        "replace": '        if False:',
        "matches": 1,
    },
    {
        "why": "subtracting two counts double-counts a row excluded for both reasons",
        "file": "tv/console_doctor.py",
        "find": "                         % (len(rows) - len(_excluded), len(rows), len(off),",
        "replace": "                         % (len(rows) - len(off) - len(nocmp), len(rows), len(off),",
        "matches": 1,
    },
    {
        "why": "an empty exemption list puts the un-actionable figure back in front of him",
        "file": "tv/console_doctor.py",
        "find": '    nocmp = [r for r in rows if r.get("comparable") is False]',
        "replace": '    nocmp = []',
        "matches": 1,
    },
]
