#!/usr/bin/env python3
"""v3009 (#81) — RETENTION SIZED FROM HIS OWN LOSS, WITH THE ONE FILE THAT ANSWERS IT PROTECTED.

The 2026-09-08 emptying was noticed ~3 days late and the oldest backup on disk was 69 hours too
young to say which backup predates the loss. His ruling: "it gets auto saved daily in a ledger
just incase if needed to restore." The policy: 48h rolling + first-of-day keepers for 90 days +
an EPISODE GUARD — while a d2r_storeEmptied episode is OPEN, the newest backup older than its
`at` is protected whatever its age, because deleting it would be the backup system deleting its
own reason to exist.

⚠ Deletion is the irreversible act, so every law here drives the SHIPPED function on a fixture
dir and counts what survived. [[unknown-stays-unknown]]
"""
import io
import json
import os
import shutil
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import control_app as CA  # noqa: E402

DAY = 24 * 3600.0


class TheBackupPruneNeverOrphansALoss(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="ledgerprune.")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.now = time.time()

    def _snap(self, name, age_s, emptied=None):
        p = os.path.join(self.d, name)
        doc = {"d2r_foundLog": "[]"}
        if emptied is not None:
            doc["d2r_storeEmptied"] = json.dumps(emptied)
        io.open(p, "w", encoding="utf-8").write(json.dumps(doc))
        t = self.now - age_s
        os.utime(p, (t, t))
        return name

    def _left(self):
        return sorted(os.listdir(self.d))

    def test_the_rolling_window_is_kept(self):
        a = self._snap("ledger_a.json", 3600)
        b = self._snap("ledger_b.json", 47 * 3600)
        r = CA._ledger_backup_prune(self.d, now=self.now)
        self.assertEqual(self._left(), sorted([a, b]))
        self.assertEqual(r["pruned"], 0)

    def test_an_old_non_keeper_is_pruned_and_the_days_first_survives(self):
        """Two snapshots on one old day: the FIRST is the keeper, the second goes."""
        first = self._snap("ledger_day_first.json", 10 * DAY + 7200)
        self._snap("ledger_day_second.json", 10 * DAY)
        fresh = self._snap("ledger_fresh.json", 60)
        r = CA._ledger_backup_prune(self.d, now=self.now)
        self.assertEqual(self._left(), sorted([first, fresh]),
                         "the day's first snapshot is the daily keeper his ruling asked for; "
                         "the day's second is redundant history")
        self.assertEqual(r["pruned"], 1)
        self.assertEqual(r["keepers"], 1)

    def test_a_keeper_older_than_ninety_days_retires(self):
        self._snap("ledger_ancient.json", 91 * DAY)
        fresh = self._snap("ledger_fresh.json", 60)
        CA._ledger_backup_prune(self.d, now=self.now)
        self.assertEqual(self._left(), [fresh])

    def test_an_open_loss_protects_the_backup_that_predates_it(self):
        """⚠ THE GUARD THAT OUTRANKS EVERY RULE. Loss at T; the newest backup OLDER than T is the
        only file that answers 'which backup predates the loss'. While the episode is OPEN it
        survives whatever its age."""
        loss_at_ms = (self.now - 100 * DAY) * 1000.0
        old = self._snap("ledger_predates.json", 101 * DAY)          # older than the loss
        self._snap("ledger_between.json", 50 * DAY)                  # after the loss, prunable
        fresh = self._snap("ledger_newest.json", 60,
                           emptied={"at": loss_at_ms, "boots": 3})   # OPEN: no recoveredAt
        r = CA._ledger_backup_prune(self.d, now=self.now)
        self.assertIn(old, self._left(),
                      "the one backup predating an OPEN loss was pruned — the backup system "
                      "deleted its own reason to exist")
        self.assertEqual(r["protected"], old)
        self.assertIn(fresh, self._left())

    def test_a_closed_loss_protects_nothing_extra(self):
        loss_at_ms = (self.now - 100 * DAY) * 1000.0
        self._snap("ledger_predates.json", 101 * DAY)
        fresh = self._snap("ledger_newest.json", 60,
                           emptied={"at": loss_at_ms, "boots": 3,
                                    "recoveredAt": (self.now - 99 * DAY) * 1000.0})
        r = CA._ledger_backup_prune(self.d, now=self.now)
        self.assertIsNone(r["protected"],
                          "a CLOSED episode is history; its predating backup ages out normally")
        self.assertNotIn("ledger_predates.json", self._left())
        self.assertIn(fresh, self._left())

    def test_an_empty_dir_is_measured_empty_not_an_error(self):
        r = CA._ledger_backup_prune(self.d, now=self.now)
        self.assertEqual(r["pruned"], 0)
        self.assertIn("measured-empty", r["why"])

    def test_a_missing_dir_deletes_nothing_and_says_so(self):
        r = CA._ledger_backup_prune(os.path.join(self.d, "nope"), now=self.now)
        self.assertEqual(r["pruned"], 0)
        self.assertIn("nothing measured", r["why"])


RED_PROOF = [
    {
        "why": "dropping the keeper branch deletes every daily save past 48h — the exact 'noticed "
               "days late with no predating backup' failure the policy exists to end",
        "file": "control_app.py",
        "find": "        if pp in keepers and age <= KEEPER_S:",
        "replace": "        if False:",
        "matches": 1,
    },
    {
        "why": "dropping the episode guard lets the prune eat the one backup that answers 'which "
               "backup predates the loss' while the loss is still open",
        "file": "control_app.py",
        "find": "        if isinstance(ev, dict) and ev.get(\"at\") and not ev.get(\"recoveredAt\"):",
        "replace": "        if False:",
        "matches": 1,
    },
    {
        "why": "a zero rolling window prunes snapshots minutes old — the corpus can no longer "
               "answer even a same-day question",
        "file": "control_app.py",
        "find": "    ROLLING_S = 48 * 3600.0",
        "replace": "    ROLLING_S = 0.0",
        "matches": 1,
    },
]

if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
