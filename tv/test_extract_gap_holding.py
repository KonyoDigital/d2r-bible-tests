#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v2772 — A NAME IS NOT A HOLDING, AND THE REPORT SAID IT WAS.

`extract_gap` computes a PANEL / FLOOR / CHRONICLE scenario for every reel (v2583) and then
decided RECOVERABLE on `has_seal and n` — the raw name count, scenario unread. Two halves of one
mechanism, forty lines apart, never joined. [[the-unjoined-end]]

MEASURED on his store before the fix:

    RECOVERABLE 4 reels / 55 names, reported as "a JOIN to fix where the seal is written"
      reel_s_1786385768689_67392   names 45   panel 0 · floor 0 · CHRONICLE 45
      the other three              names 10   panel 10

45 of the 55 — 82% of the whole recoverable gap — are Chronicle grid entries (Amulet, Ancient
Sword, Andariel's Visage, Arm of King Leoric…), a checklist of items he mostly does not own.
Joining those into a possession seal would invent 45 holdings, not recover them.

⚠ AND A SECOND READER ALREADY DISAGREED, USING THIS MODULE'S OWN CONSTANT. `read_names_lane`
filters deep rows to `EG.PANEL_SCENES` and yields evidence for 22 sessions; s_1786385768689_67392
is NOT one of them. Same reel, two answers, and the wrong one was the one on the report — which is
the finding, not an average. [[feedback-contradiction-is-the-finding]]

THE SECOND LAW HERE IS THE DENOMINATOR. `_named_sessions()` returns ({}, why) when the journal ring
will not resolve, and `n` was then 0 for every reel — so on any venue without his journal (a CI
runner, a fresh clone) twelve sealed reels printed "the reader never yielded an item name for this
session either. This one IS a capture question", which is REG-340's answer to a question nobody
managed to ask. A sealed reel now reports UNKNOWN when the names could not be measured.
[[zero-needs-a-denominator]] [[unknown-stays-unknown]]

⚠ WHAT THIS GATE DOES NOT CLAIM. It does not say the four seals were wrong to be written, and
nothing here writes or repairs a seal — back-filling one would forge the certification
frame_authority exists to protect. It pins what the REPORT may say about them.

Every law below is proven RED by a sabotage in sabotage_extract_gap_holding.py, which prints the
match count of each anchor before it applies it.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import extract_gap as EG          # noqa: E402
import frame_authority as FA      # noqa: E402


def _counts(panel=0, floor=0, chronicle=0):
    return {"names": panel + floor + chronicle, "panel": panel,
            "floor": floor, "chronicle": chronicle}


class _Patched(object):
    """Swap module attributes for the body of a with-block and always put them back.

    ⚠ THE REAL STORE IS NEVER TOUCHED. `gap()` takes `river` by injection and asks
    `frame_authority.sealed_sessions` and `EG._named_sessions` for the rest, so a fixture can
    answer all three without reading his 5.8 GB of footage or his vault_swept.json.
    [[feedback-fixtures-never-touch-live-data]]
    """

    def __init__(self, **kw):
        self.kw = kw
        self.old = {}

    def __enter__(self):
        for k, v in self.kw.items():
            mod, attr = (EG, k) if hasattr(EG, k) else (FA, k)
            self.old[k] = (mod, getattr(mod, attr))
            setattr(mod, attr, v)
        return self

    def __exit__(self, *a):
        for k, (mod, v) in self.old.items():
            setattr(mod, k, v)
        return False


def _gap(named, named_why="", seals=None, reels=("reel_s_A",)):
    """Run gap() over a fixture shelf. -> the report dict"""
    seals = {} if seals is None else seals
    with _Patched(_named_sessions=lambda *a, **k: (named, named_why),
                  sealed_sessions=lambda *a, **k: (seals, True)):
        return EG.gap(river={"rows": [{"reel": r} for r in reels]})


def _row(rep, reel="reel_s_A"):
    for r in rep.get("rows") or []:
        if r.get("reel") == reel:
            return r
    raise AssertionError("no row for %s in %r" % (reel, [x.get("reel") for x in rep.get("rows") or []]))


#: a seal shaped exactly like the ones on his disk for these reels — sealed, zero rows,
#: nothing taken. Copied in SHAPE, not in verdict: the state under test is about the NAMES.
SEAL_EMPTY = {"ts": 1, "rows": 0, "promptVer": "vp2017",
              "extracted": [], "extractedWhy": "nothing was taken"}


class TheLawItself(unittest.TestCase):
    """holding_possible() alone, with no shelf around it."""

    def test_a_chronicle_only_session_can_never_be_a_holding(self):
        ok, why = EG.holding_possible(_counts(chronicle=45))
        self.assertIs(ok, False, "45 Chronicle checklist entries read as a holding: %s" % why)
        self.assertIn("Chronicle", why, "the refusal must name WHY it refused")

    def test_a_floor_only_session_can_never_be_a_holding(self):
        """⚠ THE ARM HIS DATA DOES NOT EXERCISE. Of the four sealed reels carrying names, one is
        chronicle-only and ZERO are floor-only — so without this case the floor half of the law
        would ship unwitnessed and look covered. [[gate-blind-to-unexercised-input]]"""
        ok, why = EG.holding_possible(_counts(floor=208))
        self.assertIs(ok, False, "a floor item has no cell, so no location: %s" % why)
        self.assertIn("floor", why.lower())

    def test_one_panel_name_is_enough(self):
        ok, _ = EG.holding_possible(_counts(panel=1, floor=200, chronicle=100))
        self.assertIs(ok, True, "a container WAS open for one of these, so a cell box exists")

    def test_an_unreadable_journal_is_none_not_false(self):
        ok, why = EG.holding_possible(_counts(panel=3), names_known=False)
        self.assertIsNone(ok, "a journal nobody could read measured no holdings — it measured "
                              "NOTHING, and False is a verdict")
        self.assertIn("UNKNOWN", why)


class TheStateMachineAsksIt(unittest.TestCase):
    """The join that was missing: the verdict must move when the scenario moves."""

    def test_chronicle_only_and_sealed_is_not_recoverable(self):
        """His reel_s_1786385768689_67392, in fixture form: 45 names, all chronicle, sealed."""
        rep = _gap({"s_A": _counts(chronicle=45)}, seals={"s_A": dict(SEAL_EMPTY)})
        r = _row(rep)
        self.assertEqual(r["state"], EG.NOT_A_HOLDING,
                         "45 Chronicle names on a sealed reel reported as %s — that sends someone "
                         "to build a join that would invent 45 possessions" % r["state"])
        self.assertIs(r["holdingPossible"], False)

    def test_floor_only_and_sealed_is_not_recoverable(self):
        rep = _gap({"s_A": _counts(floor=12)}, seals={"s_A": dict(SEAL_EMPTY)})
        self.assertEqual(_row(rep)["state"], EG.NOT_A_HOLDING)

    def test_a_panel_name_still_makes_it_recoverable(self):
        """The fix may not close the gap by declaring it shut — the three real joins survive."""
        rep = _gap({"s_A": _counts(panel=6)}, seals={"s_A": dict(SEAL_EMPTY)})
        r = _row(rep)
        self.assertEqual(r["state"], EG.RECOVERABLE,
                         "6 names read with a container OPEN is exactly the join that IS owed")
        self.assertIs(r["holdingPossible"], True)

    def test_a_mixed_reel_leads_with_the_panel_names(self):
        rep = _gap({"s_A": _counts(panel=3, floor=20, chronicle=9)},
                   seals={"s_A": dict(SEAL_EMPTY)})
        self.assertEqual(_row(rep)["state"], EG.RECOVERABLE)

    def test_not_a_holding_is_not_a_capture_verdict(self):
        """NO_NAMES sends a reel to REG-340 ('film the panel'). This reader worked fine."""
        r = _row(_gap({"s_A": _counts(chronicle=45)}, seals={"s_A": dict(SEAL_EMPTY)}))
        self.assertNotIn("REG-340", r["why"],
                         "a reel whose reader produced 45 names is not a capture problem")
        self.assertIn("45", r["why"], "the names it DID read must stay visible in the verdict")

    def test_state_and_field_can_never_disagree(self):
        for c in (_counts(panel=2), _counts(chronicle=5), _counts(floor=5), _counts()):
            r = _row(_gap({"s_A": c}, seals={"s_A": dict(SEAL_EMPTY)}))
            if r["state"] == EG.RECOVERABLE:
                self.assertIs(r["holdingPossible"], True,
                              "RECOVERABLE over holdingPossible=%r — two answers, one reel"
                              % r["holdingPossible"])

    def test_every_row_carries_the_reason(self):
        rep = _gap({"s_A": _counts(chronicle=45)}, seals={"s_A": dict(SEAL_EMPTY)})
        for r in rep["rows"]:
            self.assertIn("holdingPossible", r)
            self.assertGreater(len(str(r.get("holdingWhy") or "")), 20,
                               "%s reports a holding verdict with no reason" % r.get("reel"))


class TheNameCountCarriesItsDenominator(unittest.TestCase):
    """A journal that would not open must not read as a reader that found nothing."""

    def test_a_sealed_reel_is_unknown_when_the_journal_is_dead(self):
        rep = _gap({}, named_why="the journal ring could not be resolved (boom)",
                   seals={"s_A": dict(SEAL_EMPTY)})
        r = _row(rep)
        self.assertEqual(r["state"], EG.UNKNOWN,
                         "sealed + unreadable journal reported %s — a confident capture verdict "
                         "over a file that would not open" % r["state"])
        self.assertNotIn("REG-340", r["why"])
        self.assertIs(r["namesKnown"], False)

    def test_an_unsealed_reel_may_not_claim_a_name_was_never_read(self):
        r = _row(_gap({}, named_why="the journal ring could not be resolved (boom)", seals={}))
        self.assertEqual(r["state"], EG.UNSEALED, "unsealed is a fact about the SEAL store")
        self.assertNotIn("no item name was ever read", r["why"],
                         "the name count went unmeasured; the sentence may not report a zero")

    def test_a_live_journal_still_measures_zero_as_zero(self):
        """⚠ THE OVER-CORRECTION IS THE SAME DEFECT POINTED THE OTHER WAY. A reader that really
        did yield nothing is a MEASUREMENT and must keep its capture verdict."""
        r = _row(_gap({}, seals={"s_A": dict(SEAL_EMPTY)}))
        self.assertEqual(r["state"], EG.NO_NAMES)
        self.assertIs(r["namesKnown"], True)


class TheHeadlineIsDenominated(unittest.TestCase):
    def test_recoverable_names_counts_only_panel_names(self):
        rep = _gap({"s_A": _counts(panel=3, floor=20, chronicle=9)},
                   seals={"s_A": dict(SEAL_EMPTY)})
        self.assertEqual(rep["recoverablePanelNames"], 3,
                         "the headline counted 32 names as recoverable work when 3 of them can "
                         "carry a location")

    def test_the_not_a_holding_names_are_reported_apart(self):
        rep = _gap({"s_A": _counts(chronicle=45), "s_B": _counts(panel=2)},
                   seals={"s_A": dict(SEAL_EMPTY), "s_B": dict(SEAL_EMPTY)},
                   reels=("reel_s_A", "reel_s_B"))
        self.assertEqual(rep["recoverable"], 1)
        self.assertEqual(rep["notAHolding"], 1)
        self.assertEqual(rep["notAHoldingNames"], 45)
        self.assertEqual(rep["recoverablePanelNames"], 2)
        self.assertIn("45", rep["why"], "the 45 may not vanish behind the verdict")


class HisRealStoreStillAnswers(unittest.TestCase):
    """⚠ A SAMPLE IS NOT A VERDICT — this walks the real shelf, and SKIPS where there is none.
    GitHub's runner has no reels, so a green here on CI must not be read as coverage.
    [[regression-guard]]"""

    def test_the_real_shelf_reports_a_holding_verdict_on_every_row(self):
        rep = EG.gap() or {}
        rows = rep.get("rows") or []
        if not rows:
            raise unittest.SkipTest("no reel store on this venue — measures nothing here")
        bad = [r.get("reel") for r in rows if "holdingPossible" not in r]
        self.assertEqual(bad, [], "rows with no holding verdict: %s" % bad[:3])
        for r in rows:
            if r.get("state") == EG.RECOVERABLE:
                self.assertIs(r.get("holdingPossible"), True,
                              "%s is RECOVERABLE with holdingPossible=%r"
                              % (r.get("reel"), r.get("holdingPossible")))


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
