# -*- coding: utf-8 -*-
"""v3347 (#31) — A RETIRED LOCK KEEPS ITS TESTIMONY: READABLE, NEVER BANKABLE.

HIS RULING, 2026-09-19: *"leave it off and surgically remove it we need pruning"* — remove the
`prune.arm` ceremony, do not silence it; do NOT touch `_PRUNE_SAFE_TO_RUN` or
`_PRUNE_STATS["enabled"]`; and KEEP self_arming for the other surfaces.

=== THE FIRST CUT OBEYED THE FIRST HALF AND BROKE THE LAST ===
Removing the lock, deleting `prune_wilson.py` and de-registering its gate is the removal, and it
is correct. Removing `PROVES["prune_wilson"]` alongside them looked like the same tidy-up and was
not. MEASURED on his live ledger the moment the suite went red:

    rows in .self_arming.jsonl                         349
    rows banked by prune_wilson against prune.arm       19   (newest n=18, k=18)
    _rows() after un-declaring the source             None   ← one bad row fails the whole read
    live locks still able to open                        0   of 9

Every surviving lock answered *"UNKNOWN: … has a row that could not have been banked … An
unreadable proof queue fails CLOSED"* — vault.apply, miniauto.run, prune.reports and reel.route
all sampled and all shut. So deleting one dictionary entry did the precise opposite of "keep
self_arming for other surfaces", for every surface at once, and it did it silently: the module was
behaving exactly as designed, failing closed on evidence it could not read.

=== WHAT RETIREMENT MEANS, AND WHY EACH HALF NEEDS A LAW ===
    READABLE      the pair stays in PROVES, so `_row_fault` accepts his 19 rows and the ledger
                  reads. This is his testimony and it is not mine to drop.
                  [[manual-tally-is-witness]] — once witnessed, never un-witnessed.
    NEVER BANKABLE no new evidence can land there: `bank()` already refuses any lock absent from
                  LOCKS, verified — `bank("prune.arm", …)` raises *"no such lock or route is
                  declared"*. The ceremony is gone by the removal itself, not by a new guard.
    REACHES NOTHING the 19 rows must not move a live lock. That is the clause worth PROVING rather
                  than believing, and it is measured below: dropping all 19 changes 0 of 9 scores.

⚠⚠ A STATED CONSEQUENCE, HIS TO OWN. `test_printer_wilson` used to assert that `prune.arm.after`
contained `printer.stream` — his order *"printer + reels -> theatre + shelf -> routing -> the
deleter"*. That ordering rule lived ONLY there and in the lock's own prerequisite list, so retiring
the lock removes the only place code enforced that the deleter waits for the river. **That is the
intended effect of his ruling.** `_PRUNE_SAFE_TO_RUN` survives untouched — 53 references across 20
files — and is the actual safety on the deleter. This law pins that it survives.

⚠ The ordering MECHANISM is not gone: `vault.apply` and `vault.forget` each still wait on
`vault.sweep_start`, and `TestHisOrderIsEnforced` now drives that live chain. What IS gone is any
chain longer than one step, so the advance-to-the-next-prerequisite arm is UNMEASURED rather than
passing, and says so. [[regression-guard]] §2, §6.
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import self_arming as SA  # noqa: E402

LOCK = "prune.arm"
SRC = "prune_wilson"


class TheCeremonyIsGone(unittest.TestCase):
    """His ruling's first half: removed, not silenced."""

    def test_the_lock_is_not_declared(self):
        self.assertNotIn(
            LOCK, SA.LOCKS,
            "prune.arm is a live lock again. His ruling was to REMOVE the ceremony — putting the "
            "deleter back behind Wilson evidence is a decision of his, not a restoration.")

    def test_the_harness_is_gone(self):
        self.assertFalse(
            os.path.exists(os.path.join(HERE, SRC + ".py")),
            "prune_wilson.py is back. The harness existed only to attack the retired lock; a "
            "module that can bank nowhere is a loaded gun with no target.")

    def test_its_gate_is_de_registered(self):
        import run_gates as RG
        names = [getattr(g, "name", "") for g in RG.GATES]
        self.assertNotIn(
            "test_prune_wilson", names,
            "the retired ceremony's gate is registered again, so every push pays for a suite "
            "whose subject no longer exists.")

    def test_nothing_can_bank_to_a_retired_lock(self):
        """⚠ THE DOOR, and it needs no new code — bank() refuses any lock absent from LOCKS."""
        with self.assertRaises(ValueError) as cm:
            SA.bank(LOCK, "sabotage", SRC, n=99, k=99)
        self.assertIn(
            "no such lock", str(cm.exception).lower(),
            "banking to a retired lock failed for some OTHER reason (%s). If that reason ever "
            "stops applying the retirement becomes re-openable by a single call."
            % str(cm.exception)[:120])


class TheTestimonyStillReads(unittest.TestCase):
    """His ruling's last half — the one the first cut broke."""

    def test_the_retired_pair_is_still_declared(self):
        """⚠⚠ THE CASE. This looks like dead configuration and is load-bearing."""
        self.assertIn(
            LOCK, getattr(SA, "RETIRED_LOCKS", {}),
            "prune.arm is neither a live lock nor a declared retirement, so the rows his ledger "
            "already holds for it are accounted for by nothing.")
        self.assertIn(
            LOCK, SA.PROVES.get(SRC) or (),
            "the retired pair has been dropped from PROVES. That is not a tidy-up: _row_fault "
            "then rejects his 19 rows, _rows() returns None, and EVERY lock fails CLOSED. "
            "Measured: 0 of 9 locks could open.")

    def test_a_retirement_gives_its_reason(self):
        for lk, why in getattr(SA, "RETIRED_LOCKS", {}).items():
            self.assertTrue(
                str(why or "").strip(),
                "%r is retired with no reason recorded, so the next reader cannot tell a ruling "
                "from an accident." % lk)

    def test_his_ledger_still_reads(self):
        """BEHAVIOURAL, against his real file — and honest when it is absent."""
        rows, fault = SA._rows()
        self.assertFalse(
            fault,
            "the ledger does not read: %s. A retirement that costs his banked evidence is not a "
            "surgical removal." % fault)
        if not os.path.exists(SA._ledger_path()):
            self.skipTest("no ledger on this machine — nothing banked here to keep readable")
        mine = [r for r in (rows or []) if str(r.get("src")) == SRC]
        self.assertTrue(
            mine,
            "his ledger holds no prune_wilson rows at all. 19 were measured when the ceremony was "
            "cut; if they are genuinely gone this law's premise has changed and it should be "
            "retired deliberately rather than left passing over nothing. "
            "[[regression-guard]] §4")


class RetiredEvidenceReachesNothing(unittest.TestCase):
    """⚠⚠ THE CLAUSE WORTH PROVING. Keeping the rows readable must not keep them POWERFUL."""

    def test_dropping_the_retired_rows_moves_no_live_lock(self):
        rows, fault = SA._rows()
        if fault or not rows:
            self.skipTest("ledger unreadable or empty here: %s" % (fault or "no rows"))
        without = [r for r in rows if str(r.get("src")) != SRC]
        if len(without) == len(rows):
            self.skipTest("no retired-source rows on this machine to drop")
        moved = []
        for lk in SA.LOCKS:
            a, b = SA.score(lk, rows), SA.score(lk, without)
            if (a["state"], a["n"], a["k"]) != (b["state"], b["n"], b["k"]):
                moved.append(lk)
        self.assertEqual(
            moved, [],
            "retired evidence reaches %d live lock(s): %s. Readable was never meant to mean "
            "countable — a retired harness nobody can re-derive must not be able to move a "
            "surface that still acts." % (len(moved), ", ".join(moved)))

    def test_every_retired_lock_is_declared_by_something(self):
        """A retirement whose source was ALSO dropped is the defect wearing a tidier hat."""
        for lk in getattr(SA, "RETIRED_LOCKS", {}):
            declared = [s for s, locks in SA.PROVES.items() if lk in (locks or ())]
            self.assertTrue(
                declared,
                "%r is retired and no source declares it, so any row already banked against it "
                "fails the read and takes every other lock down with it." % lk)


class TheActualSafetySurvives(unittest.TestCase):
    """⚠ HIS EXPLICIT DON'T-TOUCH. The ceremony was the ceremony; this is the safety."""

    def test_the_prune_guard_is_untouched(self):
        hits, files = 0, 0
        for fn in sorted(os.listdir(HERE)):
            if not fn.endswith(".py"):
                continue
            try:
                body = io.open(os.path.join(HERE, fn), encoding="utf-8").read()
            except Exception:
                continue
            c = body.count("_PRUNE_SAFE_TO_RUN")
            if c:
                hits += c
                files += 1
        self.assertGreaterEqual(
            hits, 40,
            "_PRUNE_SAFE_TO_RUN is down to %d reference(s) across %d file(s). It was measured at "
            "53 across 20 when the ceremony was retired, and his ruling named it explicitly as "
            "the thing NOT to touch: with the lock gone it is the only gate left on the deleter."
            % (hits, files))


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "dropping the retired pair from PROVES makes his whole ledger unreadable and fails all nine live locks CLOSED",
        "file": "tv/self_arming.py",
        "find": '    "prune_wilson": ("prune.arm",),',
        "replace": '    "prune_wilson_retired_unused": (),',
        "matches": 1,
    },
    {
        "why": "a retirement with no declaration leaves 19 banked rows accounted for by nothing",
        "file": "tv/self_arming.py",
        "find": '''RETIRED_LOCKS = {
    "prune.arm": ''',
        "replace": '''RETIRED_LOCKS = {
    "prune.arm.disabled": ''',
        "matches": 1,
    },
    {
        "why": "putting the lock back restores the ceremony his ruling removed",
        "file": "tv/self_arming.py",
        "find": '''#: ⚠⚠ RETIRED LOCKS — A REMOVED CEREMONY'S BANKED ROWS MUST STILL READ.''',
        "replace": '''LOCKS["prune.arm"] = {"surface": "THE RIVER", "acts": "deletes footage",
                      "destructive": True, "bar": 0.839, "kinds_bar": 1.8, "after": []}
#: ⚠⚠ RETIRED LOCKS — A REMOVED CEREMONY'S BANKED ROWS MUST STILL READ.''',
        "matches": 1,
    },
]
