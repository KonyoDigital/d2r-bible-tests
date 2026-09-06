# -*- coding: utf-8 -*-
"""v2736 — THE RESTORE WIRE, AND THE TWO DEFECTS A DIFFERENT MODEL FAMILY FOUND IN IT.

`ledger_restore` joins the automatic backup to the board's own apply door. It shipped in v2735
WITHOUT A SUITE — the orphan-suite gate catches a test file no gate runs, not a MODULE no test
covers, so nothing said so. This file is that suite.

=== THE TWO FINDINGS, BOTH REPRODUCED BEFORE BEING BELIEVED ===
The shipped diff was handed to a different model family and asked to refute it. Two of its three
findings were real:

1. A TRUNCATED BOARD READ BECAME A REPORTED LOSS. `board_ownership(sample=N)` slices each store
   (`fl.slice(0,n)`), so a board holding more than the cap hands back a PREFIX. `plan()` diffed the
   backup against that prefix and called everything past the cap missing.
   REPRODUCED: board truly holding 6000 against a 5000 cap -> **1000 names reported missing** that
   were never gone. Not live (his foundLog is 419) — but "not currently exceeded" is not a guard.
   FIXED in `_restore_current_from_board`, using `counts`, which the board reports INDEPENDENTLY of
   the copy. Comparing a copy against its own length is circular and could never fire.

2. (in console_doctor, gated by test_backup_loop_is_watched) a sticky `why` let a DEAD loop grade OK.

⚠ THE THIRD FINDING WAS NOT TAKEN. It argued the doctor should also age out a benign `why`
independently of the loop's own liveness stamp. Once `lastTryMs` exists that is the same fact
measured twice, and a second clock would only add a way for the two to disagree.
[[review-after-ship]] — a good reviewer earns a measurement, not obedience.
"""
import io
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

import ledger_restore as LR  # noqa: E402

ROUTE = {"id": "77f64154aaaa", "p": "main"}


def _dir_with(*blobs):
    d = tempfile.mkdtemp()
    for i, b in enumerate(blobs):
        with io.open(os.path.join(d, "ledger_2026-09-06_%06d.json" % i), "w", encoding="utf-8") as f:
            f.write(json.dumps(b))
    return d


class TheRestorePicksTheRightFileForTheRightPerson(unittest.TestCase):

    def test_an_UNROUTED_backup_is_never_attributed_to_anyone(self):
        """⚠ 59 of his 60 files predate the route stamp. They may well be his and there is no way
        to tell, and a restore that guesses is how one person's ledger lands in another's — the
        Dean defect's own shape. `restore_ledger.py` guessed by "most unique-like names"."""
        d = _dir_with({"ledger": {"foundLog": {"A": "d"}}})          # no route key at all
        hits, why = LR.backups_for(ROUTE, d)
        self.assertEqual([], hits, "an unrouted backup was matched to a profile")
        self.assertIn("predate", why, "the refusal does not say WHY the file was skipped")

    def test_a_backup_for_ANOTHER_profile_is_not_matched(self):
        d = _dir_with({"route": {"id": "someone-else", "p": "main"},
                       "ledger": {"foundLog": {"A": "d"}}})
        hits, _ = LR.backups_for(ROUTE, d)
        self.assertEqual([], hits, "another profile's backup was offered for this one")

    def test_no_route_given_refuses_rather_than_defaulting(self):
        hits, why = LR.backups_for(None, _dir_with())
        self.assertEqual([], hits)
        self.assertIn("no route", why)

    # ── ⚠⚠ FINDING 1 — THE TRUNCATION GUARD ───────────────────────────────────────────────────
    def test_a_partial_board_read_is_UNKNOWN_never_a_shortfall(self):
        d = _dir_with({"route": ROUTE,
                       "ledger": {"foundLog": {("i%d" % i): "d" for i in range(6000)}}})
        # the caller could not read the whole store, so it hands None — the contract
        out = LR.plan(ROUTE, {"foundLog": None, "setPieces": None}, d)
        self.assertTrue(out["ok"])
        self.assertIsNone(out["stores"]["foundLog"]["missing"],
                          "an unreadable store produced a missing-name list. A prefix of his "
                          "ledger is not his ledger, and reporting the remainder as lost is a "
                          "measurement of the reader, not of his data.")
        self.assertIn("UNKNOWN", out["stores"]["foundLog"]["why"])

    def test_the_guard_lives_where_the_TRUNCATION_happens(self):
        """⚠ Pinned in control_app, because plan() cannot see the cap — it is handed a list and has
        no way to know a prefix from a whole. The check must sit where `counts` is in scope."""
        src = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        self.assertIn("def _whole(store, value):", src,
                      "the truncation guard is gone from _restore_current_from_board")
        self.assertIn("if len(value) < int(want):", src,
                      "the guard no longer compares the copy against the board's INDEPENDENT "
                      "count — comparing it against its own length is circular and cannot fire")

    # ── a measured zero keeps its denominators ────────────────────────────────────────────────
    def test_nothing_missing_is_reported_WITH_both_denominators(self):
        d = _dir_with({"route": ROUTE, "ledger": {"foundLog": {"A": "d", "B": "d"}}})
        out = LR.plan(ROUTE, {"foundLog": {"A": "d", "B": "d"}, "setPieces": []}, d)
        row = out["stores"]["foundLog"]
        self.assertEqual(0, row["count"])
        self.assertEqual(2, row["inBackup"])
        self.assertEqual(2, row["onBoard"])
        # [[zero-needs-a-denominator]] — a 0 beside 2-and-2 is measured; a bare 0 is not
        self.assertIn("inBackup", row)

    def test_a_real_gap_is_named_not_only_counted(self):
        d = _dir_with({"route": ROUTE, "ledger": {"foundLog": {"Kept": "d", "Lost": "d"}}})
        out = LR.plan(ROUTE, {"foundLog": {"Kept": "d"}, "setPieces": []}, d)
        self.assertEqual(["Lost"], out["stores"]["foundLog"]["missing"])

    # ── ⚠ THE STORES THAT CANNOT TRAVEL ARE SAID, EVERY TIME ──────────────────────────────────
    def test_the_unrestorable_stores_are_declared_on_every_plan(self):
        d = _dir_with({"route": ROUTE, "ledger": {"foundLog": {}}})
        out = LR.plan(ROUTE, {"foundLog": {}, "setPieces": []}, d)
        for k in ("rwMade", "gameFound", "owned"):
            self.assertIn(k, out["notRestorableHere"],
                          "%s is backed up and cannot come back through the chronicle door, and "
                          "the plan does not say so. A restore that silently covered two of five "
                          "stores while reporting success is the worst kind." % k)

    def test_owned_is_NOT_quietly_added_to_the_restorable_set(self):
        """⚠ /api/vault_apply LOOKS like the door for `owned` and is a trap: it RE-GATES any
        caller-supplied proposal through _vault_retro() (3 witnesses, 0.55 confidence). A restore
        has a backup file, not testimony. Widening that gate to admit one would reopen the hole
        v1595 closed and a cross-family pass probed twice at v2641."""
        self.assertNotIn("owned", LR.RESTORABLE)
        self.assertIn("owned", LR.BACKED_UP_ONLY)

    # ── the proposal speaks the board's own vocabulary ────────────────────────────────────────
    def test_the_proposal_is_the_shape_the_board_already_accepts(self):
        d = _dir_with({"route": ROUTE, "ledger": {"foundLog": {"Lost": "d"},
                                                  "setPieces": ["SetLost"]}})
        out = LR.plan(ROUTE, {"foundLog": {}, "setPieces": []}, d)
        prop = LR.proposal_from(out)
        self.assertIn("wouldAdd", prop, "the board reads proposal.wouldAdd and nothing else")
        self.assertIn("Lost", prop["wouldAdd"]["uniques"])
        self.assertIn("SetLost", prop["wouldAdd"]["sets"])

    def test_a_restore_invents_no_DATE(self):
        """The board owns dating a row, exactly as it does for a hand tick. A date made up here
        would put a time on his screen that nothing witnessed."""
        d = _dir_with({"route": ROUTE, "ledger": {"foundLog": {"Lost": "Jan 1, 2026 · 00:00"}}})
        prop = LR.proposal_from(LR.plan(ROUTE, {"foundLog": {}, "setPieces": []}, d))
        self.assertEqual([], prop["wouldAdd"]["uniques"]["Lost"],
                         "the restore carried a date of its own into the board's door")

    def test_nothing_to_restore_yields_NO_proposal(self):
        d = _dir_with({"route": ROUTE, "ledger": {"foundLog": {"A": "d"}}})
        out = LR.plan(ROUTE, {"foundLog": {"A": "d"}, "setPieces": []}, d)
        self.assertIsNone(LR.proposal_from(out),
                          "an empty proposal would ask the board to apply nothing and report "
                          "success, which reads as a restore that happened")

    # ── it cannot write ───────────────────────────────────────────────────────────────────────
    def test_the_module_cannot_write_anything(self):
        import ast
        tree = ast.parse(io.open(os.path.join(HERE, "ledger_restore.py"), encoding="utf-8").read())
        WRITERS = {"dump", "dumps", "write", "writelines", "remove", "unlink", "rename",
                   "makedirs", "system", "run", "Popen", "setItem"}
        called = {n.func.attr for n in ast.walk(tree)
                  if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
        self.assertEqual(set(), called & WRITERS,
                         "ledger_restore calls %s. It reads backups and returns a PROPOSAL; the "
                         "board presses its own door. A second writer into his chronicle is the "
                         "drift this repo keeps finding." % sorted(called & WRITERS))


if __name__ == "__main__":
    unittest.main(verbosity=2)
