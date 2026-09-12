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

    #: ⚠⚠ v3014 — A PINNED CLOCK, BECAUSE THE WALL CLOCK MADE THIS GATE FLAKE 2 HOURS IN 24.
    #: The keeper law spaces two snapshots 7200s apart and expects ONE to survive as that day's
    #: first. With `now = time.time()` those two straddle a UTC midnight whenever the run happens
    #: between 00:00 and 02:00 UTC — both become first-of-day keepers and NOTHING prunes.
    #: MEASURED by sweeping `now` across all 24 hours: fails at 00:30 and 01:30 (pruned=0,
    #: keepers=2), passes the other 22. Flagged by the post-ship review before it died on a
    #: session limit; reproduced here rather than taken on its word. A green that depends on when
    #: you look is not a green. [[feedback-blind-fixture-green-gate]] [[stale-reading]]
    #: 2026-06-15 12:00:00 UTC — mid-day, so day arithmetic is stable at every offset used below.
    PINNED_NOW = 1781524800.0

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="ledgerprune.")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.now = self.PINNED_NOW

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

    def test_the_keeper_verdict_does_not_depend_on_the_hour_of_the_run(self):
        """⚠ THE FLAKE ITSELF, MADE A LAW — but the law the policy can actually keep.

        The first cut of this swept `now` across 24 hours with the fixture above (two snapshots
        7200s apart) and demanded one verdict. It went RED, and the RED was MINE: a day-bucketing
        policy is SUPPOSED to answer differently when a pair straddles a midnight, so that law
        asserted something false about the code it guards. Two snapshots two hours apart genuinely
        are on two days at 00:30 UTC.

        What IS invariant — and what the keeper test always meant — is that holding the UTC-DAY
        LAYOUT fixed, the hour you happen to run at must not change the answer. So the fixture here
        is anchored to a day boundary rather than to `now`: both snapshots sit at 12:00 and 14:00
        UTC of the same day, ten days back, whatever hour `now` is. If the verdict still moves, the
        policy is reading the clock instead of the layout. [[unknown-stays-unknown]]"""
        import calendar
        import datetime
        verdicts = {}
        for hour in range(24):
            now = calendar.timegm(datetime.datetime(2026, 6, 15, hour, 30, 0).timetuple())
            #: ⚠ TWO old days, not one. With a single day this fixture was BLIND to the day
            #: bucket being keyed off `now` instead of each file's own mtime — MEASURED: the
            #: tampered prune returned the identical (1, 1, True). Both bucketings pick the same
            #: survivor when everything is on one day, so the fixture could not tell them apart.
            #: With two days the correct policy keeps ONE PER DAY (2 keepers) and the broken one
            #: collapses every file into today's bucket and keeps a single global oldest.
            today = datetime.datetime.utcfromtimestamp(now).date()
            dayA = today - datetime.timedelta(days=10)
            dayB = today - datetime.timedelta(days=9)

            def _at(d, h):
                return calendar.timegm(
                    datetime.datetime.combine(d, datetime.time(h, 0)).timetuple())

            anchored = {
                "ledger_a_first.json": _at(dayA, 12),
                "ledger_a_later.json": _at(dayA, 14),
                "ledger_b_first.json": _at(dayB, 12),
                "ledger_b_later.json": _at(dayB, 14),
                "ledger_fresh.json": now - 60,
            }
            d = tempfile.mkdtemp(prefix="sweep.")
            self.addCleanup(shutil.rmtree, d, True)
            for name, when in anchored.items():
                p = os.path.join(d, name)
                with io.open(p, "w", encoding="utf-8") as fh:
                    fh.write(json.dumps({"d2r_foundLog": "[]"}))
                os.utime(p, (when, when))
            r = CA._ledger_backup_prune(d, now=now)
            left = set(os.listdir(d))
            verdicts[hour] = (r["pruned"], r["keepers"],
                              "ledger_a_first.json" in left, "ledger_b_first.json" in left)

        distinct = sorted(set(verdicts.values()))
        self.assertEqual(len(distinct), 1,
                         "the verdict moves with the hour of the run even though the UTC-day "
                         "layout is identical at every hour: %s — that is the clock leaking into "
                         "a day-bucketing policy" % distinct)
        #: and it must be the RIGHT single verdict, not merely a stable wrong one — the day's
        #: FIRST survives as its keeper, the second goes, the fresh one is inside 48h.
        self.assertEqual(distinct[0], (2, 2, True, True),
                         "stable, but not the keeper policy — expected each old day to keep its "
                         "OWN first (2 kept, 2 pruned, both firsts alive); got %r" % (distinct[0],))

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
    {
        #: ⚠ THIS PROOF EXISTS BECAUSE THE HOUR-SWEEP LAW WAS BLIND TO IT. Bucketing every file
        #: under TODAY keeps one global oldest instead of one per day, so every older day loses its
        #: keeper — the 90-day corpus silently collapses to a single file. With a one-day fixture
        #: the broken and correct policies returned the IDENTICAL (1, 1, True); it took a two-day
        #: fixture to separate them. Measured tampered: (3, 1, True, False).
        "why": "keying the day bucket off `now` instead of each file's own mtime collapses the "
               "whole corpus into one bucket — every day but the newest loses its keeper",
        "file": "control_app.py",
        "find": '        d = _dt.datetime.utcfromtimestamp(os.path.getmtime(pp)).strftime("%Y-%m-%d")',
        "replace": '        d = _dt.datetime.utcfromtimestamp(now).strftime("%Y-%m-%d")',
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
