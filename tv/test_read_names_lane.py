# -*- coding: utf-8 -*-
"""TWO READERS, ONE BANKING STORE, AND ONLY ONE OF THEM WAS WIRED TO IT.

His question, 2026-09-07: *"if it cant be witnessed 3 times then yes it can end up there.. but if
it witnessesed three times it automatically tallys itself right?"*

MEASURED ANSWER, on his own journal — and it is not the answer either of us expected:

    42 distinct PANEL names read by the deep lane
       3 clear the 3-witness bar  ->  Horadric Cube · Tome of Identify · Tome of Town Portal
      15 could ever tick (UNIQUE 9 · SET 5 · RUNEWORD 1)
      24 can never tick (charms, jewels, bases)

⚠⚠ THE THREE THAT CLEAR THE BAR ARE THE THREE THAT CAN NEVER TICK. His ruling names why: *"these
are locked inventory only and specifically items.. the tombs and the hordaic cub"* — carried
permanently, so present in EVERY session by construction. They are **58 of 110 sightings (52.7%)**
and the 15 grail-eligible names are 20 between them. So the auto lane's entire output is furniture,
and every real item falls to his hand. Manual is not merely the path for rares here; it is the path
for ALL FIFTEEN.

=== ⛔ WHY THIS MODULE REPORTS AND NEVER WRITES, WHICH IS THE LAW THAT MATTERS MOST ===
`reel_retention` holds a reel with the reason `rows-not-banked`. **Banking a name RELEASES that
reel's footage for pruning.** A feeder that pushed 119 never-judged names into a durable store would
hand a deleter 119 new permissions in one move, and footage has no un-delete. The split is made
visible; the existing witnessed machinery stays the only thing that writes.
[[unknown-stays-unknown]] [[feedback-fixtures-never-touch-live-data]]
"""
import ast
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

import console_doctor as D  # noqa: E402
import read_names_lane as RNL  # noqa: E402

SRC = io.open(os.path.join(HERE, "read_names_lane.py"), encoding="utf-8").read()


def _verdict():
    return dict(D.CHECKS)["read names lane"]()


class ReadNamesLane(unittest.TestCase):

    # ── ⛔ THE WRITE BAN, PROVEN FROM THE AST ─────────────────────────────────────────────────
    def test_the_lane_opens_NOTHING_for_writing(self):
        """⚠ THE LOAD-BEARING LAW. Banking releases footage; a lane that writes is a lane that can
        delete. Walks the AST rather than grepping, because a `"w"` inside a docstring explaining
        why it must not write would satisfy a text search. [[source-reading-guard]]"""
        tree = ast.parse(SRC)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fn = node.func
            name = getattr(fn, "attr", None) or getattr(fn, "id", None)
            if name not in ("open",):
                continue
            mode = None
            if len(node.args) > 1 and isinstance(node.args[1], ast.Constant):
                mode = node.args[1].value
            for kw in node.keywords or []:
                if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                    mode = kw.value.value
            if mode and any(c in str(mode) for c in ("w", "a", "+", "x")):
                self.fail("read_names_lane opens a file for writing (mode=%r). This module must "
                          "never write: banking releases footage for pruning." % mode)

    def test_the_lane_imports_no_writer(self):
        """A write can also arrive by calling somebody else's writer."""
        for bad in ("vault_apply", "chronicle_apply", "_manual_write", "apply_plan",
                    "vault_accum_write", "disk_history_append"):
            self.assertNotIn(bad + "(", SRC,
                             "read_names_lane calls %s(), which writes. This lane reports." % bad)

    # ── it uses the REAL gate, never a private copy of the rule ───────────────────────────────
    def test_it_calls_the_REAL_gate_with_the_REAL_bars(self):
        """⚠ A private reimplementation of the witness rule would drift from the rule the write
        path enforces, and the numbers this prints would then describe nothing that governs."""
        self.assertIn("VR.gate(", SRC, "the lane no longer calls vault_retro.gate")
        self.assertIn("VR.KEEP_MIN_WITNESSES", SRC, "the lane no longer defaults to the real bar")
        self.assertIn("VR.KEEP_CONF_FLOOR", SRC, "the lane no longer defaults to the real floor")
        for bad in ("len(sessions) <", "witnesses >=", "if n_w <"):
            self.assertNotIn(bad, SRC,
                             "the lane appears to re-implement the witness comparison (%r)" % bad)

    # ── ⚠ UNKNOWN IS NEVER COLLAPSED ─────────────────────────────────────────────────────────
    def test_an_unreadable_journal_is_UNKNOWN_not_an_empty_split(self):
        real = RNL.evidence
        RNL.evidence = lambda *a, **k: (None, "simulated")
        try:
            sp = RNL.split()
            self.assertFalse(sp.get("ok"), "an unreadable journal produced a confident split")
            self.assertEqual("UNKNOWN", sp.get("state"))
            st, _ = _verdict()
            self.assertEqual(D.UNKNOWN, st, "the doctor row graded an unreadable journal as a fact")
        finally:
            RNL.evidence = real

    def test_an_unreadable_ROSTER_is_UNKNOWN_not_zero_tickable(self):
        """⚠ THE EXACT ZERO I PRODUCED WHILE BUILDING THIS. Calling the roster loader by the wrong
        name handed back None, and the measurement read '0 tickable, 42 of 42 NEITHER' — a clean
        number produced by asking the wrong question. `tickable` must be None, and the row UNKNOWN.
        [[zero-needs-a-denominator]]"""
        real = RNL.rosters
        RNL.rosters = lambda *a, **k: (None, "simulated")
        try:
            sp = RNL.split()
            self.assertIsNone(sp.get("tickable"),
                              "an unreadable roster produced a tickable COUNT, which would read as "
                              "'nothing can ever tick'")
            st, say = _verdict()
            self.assertEqual(D.UNKNOWN, st, "the doctor row graded an unreadable roster: %s" % say)
        finally:
            RNL.rosters = real

    def test_an_EMPTY_roster_is_UNKNOWN_too_not_zero_tickable(self):
        """⚠⚠ THIS LAW EXISTS BECAUSE A SABOTAGE FOUND ITS SIBLING VACUOUS. The None case above
        passed while an EMPTY-but-present roster sailed through: every name classified NEITHER and
        `tickable` came back a confident 0. Relying on `load_roster` raising is leaning on another
        module's exception, not guarding. Proven by handing `rosters()` empty dicts directly."""
        real = RNL.rosters
        RNL.rosters = lambda *a, **k: ({"UNIQUE": {}, "SET": {}, "RUNEWORD": {}}, "")
        try:
            sp = RNL.split()
            self.assertIsNone(sp.get("tickable"),
                              "an EMPTY roster produced tickable=%r instead of None - a clean zero "
                              "meaning 'nothing can ever tick'" % sp.get("tickable"))
            st, say = _verdict()
            self.assertEqual(D.UNKNOWN, st, "the row graded an empty roster as a fact: %s" % say)
        finally:
            RNL.rosters = real

    def test_the_real_rosters_are_not_empty_here(self):
        """The other direction: if this venue genuinely cannot load them, say so rather than
        letting the laws above pass over a permanently-UNKNOWN module."""
        rost, why = RNL.rosters()
        if rost is None:
            self.skipTest("rosters unreadable on this venue: %s" % why)
        for k in ("UNIQUE", "SET", "RUNEWORD"):
            self.assertTrue(rost.get(k), "the %s roster is empty" % k)

    # ── ⚠⚠ THE ROW MUST BE ABLE TO GO RED ────────────────────────────────────────────────────
    def test_a_bankable_roster_name_makes_the_row_RED(self):
        """A row that can only ever be green measures nothing. RED = a name that clears the bar,
        is on a roster, and is still unbanked — work the auto door can do for free."""
        real = RNL.split
        RNL.split = lambda *a, **k: {
            "ok": True, "state": "MEASURED", "names": 42, "minWitnesses": 3,
            "tickable": 16, "autoTickable": 1, "furniture": 3,
            "auto": [{"name": "Harlequin Crest", "ledger": "UNIQUE", "witnesses": 3}],
            "manual": [], "rosterWhy": ""}
        try:
            st, say = _verdict()
            self.assertEqual(D.MISSING, st, "a bankable unbanked name was graded fine")
            self.assertIn("free", say, "the message does not say the reading is already paid for")
        finally:
            RNL.split = real

    def test_names_waiting_on_HIM_are_not_red(self):
        """⚠ THE CRY-WOLF DIRECTION. His ruling makes the manual lane CORRECT for a rare. A row
        that reds on the design working gets ignored within a week."""
        real = RNL.split
        RNL.split = lambda *a, **k: {
            "ok": True, "state": "MEASURED", "names": 42, "minWitnesses": 3,
            "tickable": 15, "autoTickable": 0, "furniture": 3,
            "auto": [], "manual": [{"name": "Harlequin Crest", "ledger": "UNIQUE",
                                    "witnesses": 1}], "rosterWhy": ""}
        try:
            st, say = _verdict()
            self.assertEqual(D.OK, st,
                             "names correctly waiting on HIS hand were graded as a fault: %s" % say)
            self.assertIn("15", say, "the message does not say how many are waiting for him")
        finally:
            RNL.split = real

    # ── the furniture list is DECLARED and closed ─────────────────────────────────────────────
    def test_the_furniture_list_is_exactly_his_three(self):
        """⚠ A HEURISTIC WOULD GROW. 'Seen in most sessions' also describes a common find, and a
        filter nobody can audit eats real items. Three names, his words."""
        self.assertEqual(("horadric cube", "tome of identify", "tome of town portal"),
                         tuple(RNL.FURNITURE),
                         "the locked-inventory list changed — it is his declared ruling, not a "
                         "tunable")

    def test_a_roster_name_can_never_be_called_furniture(self):
        """The list removes noise; it must never hide something tickable."""
        rost, why = RNL.rosters()
        if rost is None:
            self.skipTest("rosters unreadable here: %s" % why)
        for n in RNL.FURNITURE:
            self.assertNotIn(RNL.ledger_of(n, rost), ("UNIQUE", "SET", "RUNEWORD"),
                             "%r is on a roster AND on the furniture list" % n)

    def test_the_doctor_row_is_registered(self):
        self.assertIn("read names lane", dict(D.CHECKS),
                      "the row is defined but not registered, so it never runs")

    def test_it_still_parses(self):
        ast.parse(SRC)



# ══ THE EXECUTABLE RED-PROOF ═════════════════════════════════════════════════
# PROPOSED by tv/heart2_candidates.py — derived from this gate's OWN assertions and
# measured against the target file (each anchor occurs exactly once). Review it: the
# question is whether deleting this text is the defect the law exists to catch.
RED_PROOF = [
    {
        "why": 'the law requires this text in read_names_lane.py, where it occurs exactly once and in no other file the gate names; deleting it must turn the gate red',
        "file": 'read_names_lane.py',
        "find": 'VR.KEEP_MIN_WITNESSES',
        "replace": '_HEART2_TAMPERED_',
        "matches": 1,
    },
    {
        "why": 'the law requires this text in read_names_lane.py, where it occurs exactly once and in no other file the gate names; deleting it must turn the gate red',
        "file": 'read_names_lane.py',
        "find": 'VR.KEEP_CONF_FLOOR',
        "replace": '_HEART2_TAMPERED_',
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
