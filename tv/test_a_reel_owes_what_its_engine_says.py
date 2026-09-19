# -*- coding: utf-8 -*-
"""THE RIVER CONTRADICTED ITS OWN ENGINE ABOUT WHAT A REEL OWES.

`reel_router.STATIONS` has carried this promise in its own comment since it was written:

    "A reel's station is its POSITION; what it OWES is the named gate in front of it. Keeping
     those separate is the whole point - two reels can sit at the same position and owe
     different work, and one word for both is how `route` became the retention tag."

And the code four hundred lines below it wrote `"owes": OWES.get(station)` - ONE string per
station, handed unchanged to every reel standing there. A rule stated in a comment that the
adjacent code does not implement is a rule nobody is keeping, and this one was wrong on his
shelf the day it was read.

=== MEASURED 2026-09-20, LIVE, ON HIS 19 REELS ===

Two reels sit at JOIN. `extract_gap` - the engine `printer.py:508` names as this station's
authority, whose verdict has been on every printed row as `stations.extract.say` since v2572 -
gives them OPPOSITE answers:

    reel_s_1784984019250_95276    2 names, 1 read with a container OPEN   -> RECOVERABLE
    reel_s_1786385768689_67392   45 names, every one on a Chronicle page  -> NOT_A_HOLDING
         extract_gap's own why: "Nothing is owed here: it is neither a join nor a capture gap."

`reel_router._evidence` read `sealed` and `names` off that exact station dict and THREW THE
VERDICT AWAY. `_station_of` then re-derived `sealed AND names -> JOIN`, and the row handed the
second reel the sentence "sealed AND the names are on disk; the seal does not carry them. Code."

Those 45 names can never become a holding and the engine had already measured it. v2772's
`holding_possible()` is the law: a Chronicle page is a checklist of items he mostly does not
own, no container is open, so the contract's `location` has nothing to take. 45 names filed as
owed engineering work against a law that says nothing is owed. [[the-unjoined-end]] [[copy-drift]]

=== WHAT CHANGED ===
`extractSay` joins EVIDENCE_FIELDS, `_evidence` forwards `ex.get("say")` untouched, and a pure
`_owes_of(station, ev)` decides the owed work PER REEL. The row carries `owes`, `owesWhy` and
`extractSay` so a reader can check the sentence against the engine rather than trusting it.

⚠ NO REEL MOVES. The station is unchanged, `counts` is unchanged, `seal_releases_frames` is not
consulted, and nothing here can release a frame. Only the sentence changed, which is the thing
that was wrong.

⚠ THE ASYMMETRY IS THE SAFETY AND IT IS WHAT MOST OF THESE LAWS PIN. Only an EXPLICIT
NOT_A_HOLDING may downgrade the owed work to nothing. A verdict nobody could read, a word this
station does not know, a reel the engine did not answer for - every one keeps the standing gate,
because the direction that costs something is announcing nothing is owed when nobody could tell.
[[unknown-stays-unknown]]
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

# ⚠ v3379 — MAKE STDOUT SURVIVE HIS CONSOLE BEFORE ANYTHING PRINTS. This file's messages carry
# non-ASCII, and his operator console is cp1255: without this the gate PASSES its check and then
# dies inside the print that reports it, so a clean tree exits non-zero for a reason that has
# nothing to do with the code. REG-044 / REG-054 / REG-077 are the same bug three times, and the
# pre-push gate refused this very push for it. [[windows-powershell-gotchas]]
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import reel_router as RR


class _PatchedStream(object):
    """Drive `_evidence` off a printed report we control. -> context manager

    ⚠ IT PATCHES `printer.stream`, NOT `_evidence` ITSELF. Stubbing the function under test is
    how a law ends up grading its own fixture; this hands the real function the real shape it
    reads and lets it do its own work. [[feedback-blind-fixture-green-gate]]
    """

    def __init__(self, extract):
        self.extract = extract
        self._old = None

    def __enter__(self):
        import printer as P
        self._old = P.stream
        rows = [{"reel": "reel_fixture_1", "stations": {
            "extract": dict(self.extract),
            "template": {"say": "known", "worthReading": True},
        }}]
        P.stream = lambda reel=None: {"ok": True, "rows": rows}
        return self

    def __exit__(self, *a):
        import printer as P
        P.stream = self._old
        return False


class AReelOwesWhatItsEngineSays(unittest.TestCase):

    # ── the defect itself ──────────────────────────────────────────────────────────────────
    def test_a_NOT_A_HOLDING_reel_at_JOIN_owes_nothing(self):
        """The 45-chronicle-name reel. The engine already ruled it; the river must not re-derive."""
        text, why = RR._owes_of("JOIN", {"extractSay": "NOT_A_HOLDING"})
        self.assertNotEqual(text, RR.OWES["JOIN"],
                            "a reel its own engine rules NOT_A_HOLDING was handed the standing "
                            "JOIN gate - the river is still re-deriving a verdict it was given")
        self.assertEqual(text, RR.NOTHING_OWED)
        self.assertIn("NOT_A_HOLDING", why,
                      "the sentence must CITE the engine, or a row reading NOTHING is "
                      "indistinguishable from a row nobody asked about")

    def test_a_RECOVERABLE_reel_at_JOIN_STILL_owes_the_join(self):
        """⚠ THE BASELINE, and it is the half that matters most.

        The cheap way to stop the river over-claiming is to stop it claiming anything, which
        would erase the ONE real join on his shelf while looking exactly like a fix.
        """
        text, why = RR._owes_of("JOIN", {"extractSay": "RECOVERABLE"})
        self.assertEqual(text, RR.OWES["JOIN"],
                         "the only genuinely recoverable reel on his shelf stopped owing its "
                         "join - the fix has silenced the station instead of correcting it")
        self.assertIn("RECOVERABLE", why)

    # ── UNKNOWN never becomes "nothing owed" ──────────────────────────────────────────────
    def test_a_reel_the_engine_did_not_answer_for_keeps_the_standing_gate(self):
        for ev in ({"extractSay": None}, {}, None, "not a dict", 0):
            text, why = RR._owes_of("JOIN", ev)
            self.assertEqual(text, RR.OWES["JOIN"],
                             "ev=%r downgraded the owed work with no verdict to stand on" % (ev,))
            self.assertIn("UNKNOWN", why,
                          "ev=%r produced no UNKNOWN reason - a missing verdict must SAY it is "
                          "missing, not quietly reuse the standing text" % (ev,))

    def test_a_verdict_this_station_does_not_know_keeps_the_standing_gate(self):
        """A sixth state added to extract_gap must not silently read as 'nothing owed' here."""
        for say in ("NO_NAMES", "UNSEALED", "UNKNOWN", "SOMETHING_NEW", ""):
            text, _ = RR._owes_of("JOIN", {"extractSay": say})
            self.assertEqual(text, RR.OWES["JOIN"],
                             "extractSay=%r was allowed to change the owed work" % (say,))

    # ── containment: this touches exactly one station ────────────────────────────────────
    def test_no_station_but_JOIN_is_touched(self):
        for st in RR.STATIONS:
            for say in ("NOT_A_HOLDING", "RECOVERABLE", None, "NO_NAMES"):
                text, why = RR._owes_of(st, {"extractSay": say})
                if st == "JOIN":
                    continue
                self.assertEqual(text, RR.OWES.get(st),
                                 "%s/%r changed - the per-reel override has leaked out of JOIN, "
                                 "which is where its measurement was taken" % (st, say))
                self.assertEqual(why, "")

    def test_the_river_does_not_grow_a_tenth_lane(self):
        """NOTHING_OWED is a per-reel sentence, never a station.

        `_label_of` derives the shelf's lane names from `OWES`, and his ruling on those lanes was
        explicit. A per-reel override living in that map would invent a lane he never asked for.
        """
        self.assertNotIn(RR.NOTHING_OWED, list(RR.OWES.values()))
        self.assertEqual(len(RR.labels()), len(RR.STATIONS))

    # ── the join itself: the engine's verdict reaches the evidence ───────────────────────
    def test_the_evidence_carries_the_engines_own_verdict(self):
        with _PatchedStream({"say": "NOT_A_HOLDING", "sealed": True, "names": 45}):
            ev, _why = RR._evidence()
        self.assertEqual((ev.get("reel_fixture_1") or {}).get("extractSay"), "NOT_A_HOLDING",
                         "the printer put extract_gap's verdict on the row and the evidence "
                         "dropped it again - the join is cut at the same place it always was")

    def test_an_absent_verdict_arrives_as_None_and_not_as_a_word(self):
        with _PatchedStream({"sealed": True, "names": 2}):
            ev, _why = RR._evidence()
        self.assertIsNone((ev.get("reel_fixture_1") or {}).get("extractSay"),
                          "a station with no verdict must reach the decider as UNKNOWN")

    def test_the_verdict_is_declared_evidence_so_a_later_edit_may_read_it(self):
        self.assertIn("extractSay", RR.EVIDENCE_FIELDS)

    # ── reachability, not presence ───────────────────────────────────────────────────────
    def test_the_printed_row_actually_ASKS_the_per_reel_function(self):
        """⚠ A PRESENCE LAW WOULD PASS OVER A DEAD CALL.

        This replaces `_owes_of` and proves the ROW changes, so re-inlining `OWES.get(station)`
        at the append site fails here even though every other law in this file still passes.

        ⚠ IT DRIVES THE REAL `route()` OFF A FIXTURE SHELF, so it runs on a runner that has never
        seen his footage. The first cut read the live shelf and would have gone RED on CI rather
        than skipping: measured, a venue whose printer answers ok with no rows returns
        `ok=True, reels=0`, and the "nothing was graded" assertion would have fired. A law whose
        failure mode is the VENUE is the defect [[test-venue]] [[regression-guard]].
        """
        old = RR._owes_of
        try:
            RR._owes_of = lambda station, ev: ("SENTINEL-%s" % station, "sentinel-why")
            with _PatchedStream({"say": "NOT_A_HOLDING", "sealed": True, "names": 45}):
                rep = RR.route()
            rows = rep.get("reels") or []
            self.assertTrue(rows, "the fixture shelf produced no row - the harness is broken, "
                                  "which is an instrument failure and never a pass")
            for r in rows:
                self.assertEqual(r.get("owes"), "SENTINEL-%s" % r.get("station"),
                                 "%s kept the station text while _owes_of was replaced - the "
                                 "row is not asking it" % r.get("reel"))
                self.assertEqual(r.get("owesWhy"), "sentinel-why")
        finally:
            RR._owes_of = old

    def test_the_whole_chain_carries_the_verdict_from_printer_to_printed_row(self):
        """END TO END, on a venue with no footage: printed station -> evidence -> owed work.

        Every other law here grades ONE link. This one runs the real `_evidence`, the real
        `_station_of` and the real `_owes_of` over a printed row and requires the sentence that
        comes out the far end to match the verdict that went in — which is the join itself.
        """
        with _PatchedStream({"say": "NOT_A_HOLDING", "sealed": True, "names": 45}):
            rep = RR.route()
        rows = rep.get("reels") or []
        self.assertEqual(len(rows), 1, "the fixture shelf produced %d rows" % len(rows))
        r = rows[0]
        self.assertEqual(r.get("station"), "JOIN",
                         "the station moved - this change was supposed to move NO reel")
        self.assertEqual(r.get("extractSay"), "NOT_A_HOLDING")
        self.assertEqual(r.get("owes"), RR.NOTHING_OWED)

        with _PatchedStream({"say": "RECOVERABLE", "sealed": True, "names": 2}):
            rep2 = RR.route()
        r2 = (rep2.get("reels") or [{}])[0]
        self.assertEqual(r2.get("station"), "JOIN")
        self.assertEqual(r2.get("owes"), RR.OWES["JOIN"],
                         "the recoverable case lost its join through the full chain")

    def test_the_retention_guard_actually_WATCHES_the_new_decider(self):
        """⚠ THE ROSTER ENTRY IS PROVEN LIVE, NOT READ.

        `_string_keys_read_by` does not recurse into callees, so `route`'s entry cannot cover
        `_owes_of` - that is the hole v2770 found for `_routed_by_a_lane`. This puts a keep-reason
        INTO `_owes_of` and requires the guard to go red, which a missing roster entry cannot do.
        """
        ok, findings = RR.assert_independent_of_retention()
        self.assertTrue(ok, "the guard is already red before the drill: %s" % findings)

        def _tampered(station, ev):
            return (ev or {}).get("holdKind"), ""

        old = RR._owes_of
        try:
            RR._owes_of = _tampered
            ok2, findings2 = RR.assert_independent_of_retention()
        finally:
            RR._owes_of = old
        self.assertFalse(ok2, "a keep-reason read inside _owes_of did NOT turn the guard red - "
                              "the new decider is outside the roster and nothing is watching it")
        self.assertTrue(any("holdKind" in f for f in findings2), findings2)

    # ── and on his actual shelf ──────────────────────────────────────────────────────────
    def test_on_his_shelf_every_row_agrees_with_its_own_engine(self):
        rep = RR.route()
        if not rep.get("ok"):
            self.skipTest("no shelf to route on this venue: %s" % rep.get("why"))
        rows = rep.get("reels") or []
        if not rows:
            # ⚠ A RUNNER HAS NO FOOTAGE, AND THAT IS NOT A FAILURE. Measured: a printer that
            # answers ok over an absent shelf returns ok=True with 0 rows. This law is the LIVE
            # half and is honestly venue-dependent; the other 11 run everywhere, and the fixture
            # law above covers this same chain end to end. [[regression-guard]] a skip is not a pass.
            self.skipTest("this venue has no reels on the shelf - nothing to grade against")
        seen = 0
        for r in rows:
            want, _ = RR._owes_of(r.get("station"), r)
            self.assertEqual(r.get("owes"), want,
                             "%s prints %r while its own evidence says %r"
                             % (r.get("reel"), r.get("owes"), want))
            if r.get("station") == "JOIN":
                seen += 1
                self.assertIsNotNone(r.get("extractSay"),
                                     "%s sits at JOIN with no engine verdict on the row" % r.get("reel"))
        print("   graded %d reel(s); %d at JOIN" % (len(rows), seen))


#: ⚠ EVERY ONE OF THESE MUST BE SEEN RED. The two shelf-driven laws skip on a venue with no
#: footage, so the proofs are aimed at arms the fixture-driven laws reach as well - a proof that
#: only fails a skipped case proves nothing about CI. [[regression-guard]]
RED_PROOF = [
    {
        'why': 'the whole defect: with the NOT_A_HOLDING arm dead, the 45-chronicle-name reel is '
               'handed the standing JOIN gate again and told the seal owes it code. '
               'test_a_NOT_A_HOLDING_reel_at_JOIN_owes_nothing must fail.',
        'file': 'reel_router.py',
        'find': '    if say == "NOT_A_HOLDING":',
        'replace': '    if False and say == "NOT_A_HOLDING":',
        'matches': 1,
    },
    {
        'why': 'THE DIRECTION THAT COSTS SOMETHING. Let an unanswered engine mean "nothing owed" '
               'and a reel nobody could measure reads as settled work. '
               'test_a_reel_the_engine_did_not_answer_for_keeps_the_standing_gate must fail.',
        'file': 'reel_router.py',
        'find': '''    if say is None:
        return base, ("extract_gap did not answer''',
        'replace': '''    if say is None:
        return NOTHING_OWED, ("extract_gap did not answer''',
        'matches': 1,
    },
    {
        'why': 'THE BASELINE. Silencing JOIN wholesale looks identical to fixing it, and would '
               'erase the one genuinely recoverable reel on his shelf. '
               'test_a_RECOVERABLE_reel_at_JOIN_STILL_owes_the_join must fail.',
        'file': 'reel_router.py',
        'find': '    if say == "RECOVERABLE":\n        return base, (',
        'replace': '    if say == "RECOVERABLE":\n        return NOTHING_OWED, (',
        'matches': 1,
    },
    {
        'why': 'let the override escape JOIN and a CAPTURE reel starts announcing nothing is '
               'owed. test_no_station_but_JOIN_is_touched must fail.',
        'file': 'reel_router.py',
        'find': '    if station != "JOIN":',
        'replace': '    if station not in ("JOIN", "CAPTURE"):',
        'matches': 1,
    },
    {
        'why': 'CUT THE JOIN AT THE PLACE IT WAS ALWAYS CUT: the evidence stops forwarding the '
               'printed verdict. test_the_evidence_carries_the_engines_own_verdict must fail.',
        'file': 'reel_router.py',
        'find': '            "extractSay": ex.get("say"),',
        'replace': '            "extractSay": None,',
        'matches': 1,
    },
    {
        'why': 'RE-INLINE THE STATION TEXT AT THE APPEND SITE - the exact regression a presence '
               'law would sail past, since _owes_of would still exist and still be correct. '
               'test_the_printed_row_actually_ASKS_the_per_reel_function must fail.',
        'file': 'reel_router.py',
        'find': '        _owes, _owes_why = _owes_of(station, _e)',
        'replace': '        _owes, _owes_why = (OWES.get(station), "")',
        'matches': 1,
    },
    {
        'why': 'drop the new decider out of the retention guard\'s roster. Nothing else goes red '
               '- route() still passes - which is precisely the hole v2770 found. '
               'test_the_retention_guard_actually_WATCHES_the_new_decider must fail.',
        'file': 'reel_router.py',
        'find': '''        (_owes_of, RETENTION_FIELDS,
         "decides what THIS reel owes at its station"),''',
        'replace': '',
        'matches': 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
