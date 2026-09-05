#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CF-5 — A FALSE ALARM THAT BLINDED A REAL WATCHDOG FOR 7.8 DAYS.

⚠⚠ WHAT WAS MEASURED, 2026-09-05, on his live `board_tally.json`:

    ownerId    77f641…                       <- resolved authoritatively 34 lines upstream
    contested  77f641…|main  293/121         <- fresh, advancing every 60s
               c5c2c9…|main  280/120         <- SEVEN POINT EIGHT DAYS old and frozen

293 > 280 AND 121 > 120 — strictly greater in BOTH lanes, which is exactly what one monotonic
adds-only counter sampled twice must look like. It is the same board across an install-id re-mint
(the v2220 note records both worlds reading 120/280 at that moment, and the frozen row is still
exactly 120/280), not two worlds disagreeing. The filed row said "290 vs 280"; it was stale too.

THE OMISSION: the predicate had no staleness term at all, so a week-old frozen reading counted as
a live claim against a row advancing every 60 seconds.

⚠⚠ AND MY FIRST FIX WAS WRONG TWICE — v2214's OWN GUARD CAUGHT IT, WHICH IS THE POINT OF HAVING IT.
  · I filtered by `doc["ownerId"]`. v2214 forbids exactly that: *"'Empty prefix means owner' is a
    coincidence, not a decision procedure"* — two worlds that both claim him and DISAGREE must be
    REPORTED, never RESOLVED, because silently preferring one is the defect it was written for.
    Withdrawn.
  · I measured freshness against the WALL CLOCK. v2214's fixture posts at `at=1000`/`2000` — 1970 —
    so a "within 3 days of now" window discards BOTH rows and the alarm becomes unreachable in
    every test. A fixture that cannot reach the state it grades is not evidence about that state.

What actually separates the two situations is whether the readings are CONTEMPORARY. Two worlds
sampled a second apart that disagree are a real conflict at any date; a row left a week behind the
newest is a memory, not a claimant. So the window is relative to the NEWEST reading — true for his
live file (7.8 days behind) and for the fixture (1 second apart) alike.

⚠⚠ AND THE COST WAS NOT THE WRONG SENTENCE. `console_doctor` did
`if doc.get("contested"): return MISSING` **before** its high-water/drop check, so the detector for
*"his published progress is BELOW its own high-water mark"* — the one that catches a ledger entry
vanishing — was UNREACHABLE the whole time. **A warning that returns before a detector has
silently switched that detector off.**

⚠⚠⚠ AND UN-BLINDING IT MADE A LATENT DEFECT REACHABLE ON THE SAME DAY. `recent = drops[-1]` took
the last row in the file, which is a TEST FIXTURE sitting in his live store:
`{"route": "real-1|main", "lane": "runewords", "from": 42, "to": 0, "at": null}`. The first time
his progress ever fell, the sentence would have reported a fixture's fall as his, dated 1970.
Measured: 1 of his 4 drop rows is actually his. Fixing a blindness obliges you to check what the
newly-sighted code says. [[sweep-dont-ask]]

⚠ NOTHING IS PRUNED. The fixture row is his file's content and stays exactly where it is; it is
simply no longer read as his.
"""
import os
import sys
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import console_doctor as CD  # noqa: E402

OWN = "77f641548cfa405693a0d6978946e25d"
FOREIGN = "c5c2c92d9fd049a38dfe2e46728e5eca"
FRESH_MS = 3 * 24 * 3600 * 1000


def _row(oid, at, sets, uni, pfx=""):
    return {"who": {"id": oid, "p": "main", "pfx": pfx}, "at": at,
            "sets": {"have": sets, "total": 135}, "uniques": {"have": uni, "total": 403},
            "runewords": {"have": 99, "total": 99}}


def _live(owners, own=None, now=None):
    """The predicate as shipped in control_app: CONTEMPORARY with the newest reading.

    ⚠ `own` is accepted and IGNORED, deliberately. My first cut filtered by ownerId and v2214's
    guard refused it: *"'Empty prefix means owner' is a coincidence, not a decision procedure"* —
    two worlds that both claim him and DISAGREE must be REPORTED, not RESOLVED. The parameter is
    kept only so a caller that passes it cannot silently change the answer.
    """
    ats = [r.get("at") for _, r in owners
           if isinstance(r.get("at"), (int, float)) and not isinstance(r.get("at"), bool)]
    newest = max(ats) if ats else None
    return [(k, r) for k, r in owners
            if newest is None
            or (isinstance(r.get("at"), (int, float)) and not isinstance(r.get("at"), bool)
                and (newest - r["at"]) <= FRESH_MS)]


class AWorldTheOwnerCheckExcludedIsNotACoClaimant(unittest.TestCase):

    def test_his_REAL_pair_is_not_contested(self):
        """★ The exact rows from his store, with their real timestamps."""
        now = int(time.time() * 1000)
        owners = [("77f641…|main", _row(OWN, 1788565093100, 121, 293)),
                  ("c5c2c9…|main", _row(FOREIGN, 1787889882250, 120, 280))]
        live = _live(owners, OWN, now)
        self.assertEqual(len(live), 1, "a foreign world is still counted as a co-claimant")
        self.assertFalse(len(live) > 1)

    def test_a_row_far_BEHIND_THE_NEWEST_is_not_a_live_claim(self):
        """Whoever owns it. A reading a week behind the newest is a memory, not a claimant."""
        now = int(time.time() * 1000)
        owners = [("a|main", _row(OWN, now, 121, 293)),
                  ("b|main", _row(FOREIGN, now - 9 * 86400000, 80, 200))]
        self.assertEqual(len(_live(owners, OWN, now)), 1)

    def test_ANCIENT_but_CONTEMPORARY_readings_still_contest(self):
        """★★ THE ONE MY FIRST CUT BROKE. v2214's fixture posts at at=1000 and at=2000 — 1970 by
        the wall clock. A wall-clock freshness window discards BOTH and the alarm becomes
        unreachable in every test, which is a fixture that cannot reach the state it grades.
        Relative-to-newest keeps them contemporary and the conflict visible.
        [[feedback-blind-fixture-green-gate]]"""
        owners = [("a|main", _row(OWN, 1000, 120, 280)),
                  ("b|main", _row(FOREIGN, 2000, 117, 266))]
        self.assertEqual(len(_live(owners, OWN)), 2,
                         "two readings one second apart were discarded as stale because they are "
                         "old in wall-clock terms")

    def test_it_does_NOT_resolve_by_ownerId(self):
        """★★ v2214's RULE, and my first cut violated it. Two worlds that both claim him and
        DISAGREE must be REPORTED. Filtering to `ownerId` silently prefers one, which is the exact
        defect that guard was written for."""
        now = int(time.time() * 1000)
        owners = [("a|main", _row(OWN, now, 120, 280)),
                  ("b|main", _row(FOREIGN, now - 1000, 117, 266))]
        self.assertEqual(len(_live(owners, OWN, now)), 2,
                         "the foreign world was filtered out — that is resolving, not reporting")

    def test_TWO_FRESH_worlds_of_his_that_DISAGREE_still_contest(self):
        """⚠⚠ THE BASELINE. A filter that silences everything is not a filter — the alarm must
        still be able to fire, or this fix has merely traded a false positive for a blind spot."""
        now = int(time.time() * 1000)
        owners = [("a|main", _row(OWN, now, 121, 293)),
                  ("b|main", _row(OWN, now - 3600000, 118, 280))]
        live = _live(owners, OWN, now)
        self.assertEqual(len(live), 2)
        figs = {tuple((r.get(k) or {}).get("have") for k in ("sets", "uniques", "runewords"))
                for _, r in live}
        self.assertTrue(len(figs) > 1, "two fresh disagreeing worlds no longer register")

    def test_an_unreadable_timestamp_is_not_treated_as_fresh(self):
        now = int(time.time() * 1000)
        for bad in (None, "yesterday", True):
            owners = [("a|main", _row(OWN, now, 121, 293)),
                      ("b|main", _row(OWN, bad, 80, 200))]
            self.assertEqual(len(_live(owners, OWN, now)), 1,
                             "at=%r was treated as a live claim" % (bad,))


class TheWarningMayNotBlindTheDetector(unittest.TestCase):
    """★★ THE STRUCTURAL BUG. A warning that returns before a check switches that check off."""

    def test_the_contested_branch_no_longer_returns(self):
        import inspect
        src = inspect.getsource(CD)
        i = src.index('_contested_say = (')
        window = src[max(0, i - 700):i]
        self.assertNotIn('return MISSING, ("TWO worlds', window,
                         "the contested branch still returns before the high-water check")

    def test_the_high_water_check_is_reachable_on_his_live_store(self):
        """Drives the real doctor against the real file. If this ever returns MISSING with a
        contested sentence, the short-circuit is back."""
        rows = CD.run(include_slow=False)
        hit = [r for r in rows if "progress" in str(r.get("check", "")).lower()]
        if not hit:
            self.skipTest("no progress check in this doctor run — a skip is not a pass")
        r = hit[0]
        self.assertIn(r.get("state"), ("ok", "OK", "MISSING", "UNKNOWN"))
        self.assertNotIn("TWO worlds are both claiming", str(r.get("why") or ""),
                         "the contested sentence is still standing in for the real verdict")


class ADropIsOnlyHisIfItIsHisWorld(unittest.TestCase):
    """⚠ Reachable ONLY because this same version un-blinded the check above it."""

    def test_it_takes_the_last_drop_of_HIS_route_not_the_last_row(self):
        key = "77f641…|main"
        drops = [{"route": key, "lane": "sets", "from": 121, "to": 120, "at": 1788048199995},
                 {"route": "real-1|main", "lane": "runewords", "from": 42, "to": 0, "at": None}]
        mine = [d for d in drops if d.get("route") == key]
        self.assertEqual(len(mine), 1)
        self.assertEqual(mine[-1]["lane"], "sets",
                         "the fixture's runewords 42->0 would be reported as his")
        self.assertIsNotNone(mine[-1]["at"], "his drop carries a real date; the fixture's is null")

    def test_no_drop_of_his_is_an_HONEST_EMPTY_not_someone_elses_row(self):
        drops = [{"route": "real-1|main", "lane": "runewords", "from": 42, "to": 0, "at": None}]
        mine = [d for d in drops if d.get("route") == "77f641…|main"]
        self.assertEqual(mine, [], "a foreign drop was adopted as his")

    def test_the_shipped_code_filters_by_route(self):
        import inspect
        src = inspect.getsource(CD)
        self.assertIn('d.get("route") == key', src,
                      "console_doctor still takes drops[-1] regardless of whose world it is")


class TheHighWaterKeyIsChosenNotStumbledOn(unittest.TestCase):

    def test_it_prefers_ownerId_over_dict_order(self):
        import inspect
        src = inspect.getsource(CD)
        i = src.index("_own = str(doc.get(\"ownerId\") or \"\")")
        j = src.index('w.get("pfx") == ""', i)
        self.assertIn('str(w.get("id") or "") == _own', src[i:j],
                      "the high-water key is still picked by iteration order")

    def test_the_pfx_fallback_survives_for_a_doc_with_no_ownerId(self):
        """⚠ An older doc carries no ownerId. Removing the fallback would make this UNKNOWN for
        every historic file — trading a guess for a blindness."""
        import inspect
        src = inspect.getsource(CD)
        self.assertIn('if not key:', src)


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
