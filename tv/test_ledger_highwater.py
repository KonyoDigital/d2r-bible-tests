# -*- coding: utf-8 -*-
"""A14 — a counter that only goes up needs a STORED peak, and the peak must not be seeded from a loss.

⚠⚠ THE DEFECT THIS FILE CAUGHT FIRST WAS IN THE MODULE'S OWN FIRST ACT. `seed()` recorded the
LATEST snapshot as the peak — so if the ledger had already dropped before the peak file existed,
the reduced number became the peak and the loss was invisible for ever. That is precisely the
failure the module exists to prevent, built into how it starts. It seeds from the highest value
across every readable snapshot now.

⚠ Measured on his 60 real snapshots before any of this was built: foundLog 412→416, owned 169,
setPieces 120→121, and ZERO consecutive drops in the whole window. So this ships GREEN — it is
insurance, not a fix for a live bug.

⚠ And the window BEGINS AFTER the loss that inspired it (foundLog 412; the 2026-08-28 drop to 383
is outside it). A clean window is not a clean history. [[unknown-stays-unknown]]
"""
import io
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import ledger_highwater as LH   # noqa: E402


class ThePeakMustNotBeSeededFromALoss(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="lhw_")
        self.snaps, self.peaks = LH.SNAPS, LH.PEAKS
        LH.SNAPS = os.path.join(self.dir, "snaps")
        LH.PEAKS = os.path.join(self.dir, "peaks.json")
        os.makedirs(LH.SNAPS)

    def tearDown(self):
        LH.SNAPS, LH.PEAKS = self.snaps, self.peaks

    def _snap(self, stamp, **counts):
        p = os.path.join(LH.SNAPS, "ledger_%s.json" % stamp)
        io.open(p, "w", encoding="utf-8").write(json.dumps(
            {"ledger": {k: list(range(v)) for k, v in counts.items()}}))
        return p

    def test_seeding_after_a_drop_records_the_HIGH_not_today(self):
        """⚠ THE MODULE'S OWN FIRST ACT WAS THE BUG. Seed from `latest()` and a ledger that has
        already lost entries locks the loss in as the peak."""
        self._snap("2026-01-01_010101", foundLog=416)
        self._snap("2026-01-02_010101", foundLog=400)      # the loss, already happened
        LH.seed()
        peak = json.load(io.open(LH.PEAKS, encoding="utf-8"))["foundLog"]["peak"]
        self.assertEqual(
            peak, 416,
            "the peak was seeded at %d — the value AFTER a loss. A counter seeded from today can "
            "never see a drop that happened before today, which is the one thing this module is "
            "for." % peak)
        r = LH.report()
        self.assertEqual(r["state"], LH.BELOW_PEAK,
                         "with the peak correctly at 416 and the ledger at 400, the report says "
                         "%r" % r["state"])

    def test_re_seeding_cannot_lower_the_bar_once_history_is_ROTATED_AWAY(self):
        """A mechanism that forgets on request is not a ratchet.

        ⚠ MY FIRST VERSION OF THIS TEST PASSED ON THE SABOTAGE. Removing the `v <= old` guard
        changed nothing, because `historic_peaks()` takes the maximum across every snapshot and
        the high was still on disk to be re-found. The guard is not redundant — it protects the
        STORED peak when the history that proved it has been ROTATED AWAY, which is the only
        state where the two disagree. A guard that cannot be shown to matter is one someone
        deletes while tidying, so the test now exercises the case it is actually for.
        """
        self._snap("2026-01-01_010101", foundLog=416)
        LH.seed()
        peak = json.load(io.open(LH.PEAKS, encoding="utf-8"))["foundLog"]["peak"]
        self.assertEqual(peak, 416, "BASELINE: the peak was not recorded at all")

        # the old snapshot ages out, and the only remaining history shows the reduced count
        os.unlink(os.path.join(LH.SNAPS, "ledger_2026-01-01_010101.json"))
        self._snap("2026-01-02_010101", foundLog=400)
        LH.seed()                                          # run again, with the proof gone
        peak = json.load(io.open(LH.PEAKS, encoding="utf-8"))["foundLog"]["peak"]
        self.assertEqual(
            peak, 416,
            "re-seeding lowered the peak to %d after the snapshot proving 416 was rotated away. "
            "The stored peak is then only as durable as the oldest file on disk, and a loss "
            "outlives its own evidence." % peak)
        self.assertEqual(LH.report()["state"], LH.BELOW_PEAK)

    def test_a_standing_loss_is_reported_until_reconciled(self):
        self._snap("2026-01-01_010101", foundLog=416)
        LH.seed()
        self._snap("2026-01-02_010101", foundLog=410)
        self._snap("2026-01-03_010101", foundLog=410)
        self._snap("2026-01-04_010101", foundLog=410)      # settled — a pairwise diff is clean now
        r = LH.report()
        self.assertEqual(
            r["state"], LH.BELOW_PEAK,
            "three snapshots after the drop the count is stable, so a two-newest comparison sees "
            "nothing. The peak must still report it — that is the whole reason this exists.")
        self.assertIn("foundLog", r["below"])

    def test_accept_lowers_the_peak_only_with_a_reason_and_records_it(self):
        """⚠ A ratchet with no reconcile path goes permanently red the first time he removes
        something on purpose, and a row that is always red is a row he learns to skip."""
        self._snap("2026-01-01_010101", foundLog=416)
        LH.seed()
        self._snap("2026-01-02_010101", foundLog=410)
        self.assertFalse(LH.accept("foundLog", "")["ok"],
                         "a peak was lowered with no reason given")
        self.assertTrue(LH.accept("foundLog", "sold six duplicates on purpose")["ok"])
        rec = json.load(io.open(LH.PEAKS, encoding="utf-8"))["foundLog"]
        self.assertEqual(rec["peak"], 410)
        self.assertEqual(rec["acceptedFrom"], 416,
                         "the accepted change does not record what it replaced")
        self.assertIn("duplicates", rec["reason"])
        self.assertEqual(LH.report()["state"], LH.OK)

    def test_no_snapshots_is_UNKNOWN_not_an_intact_ledger(self):
        r = LH.report()
        self.assertEqual(r["state"], LH.UNKNOWN)
        self.assertIn("UNKNOWN", r["why"])

    def test_no_peak_recorded_is_UNKNOWN_not_OK(self):
        self._snap("2026-01-01_010101", foundLog=416)
        r = LH.report()
        self.assertEqual(
            r["state"], LH.UNKNOWN,
            "with no peak ever recorded it reported %r. Nothing can be below a peak that does not "
            "exist, and calling that OK is a clean bill nobody earned." % r["state"])

    def test_an_absent_key_is_not_a_key_worth_zero(self):
        self._snap("2026-01-01_010101", foundLog=416, setPieces=121)
        LH.seed()
        self._snap("2026-01-02_010101", foundLog=416)      # setPieces absent entirely
        r = LH.report()
        keys = [row["key"] for row in r["rows"]]
        self.assertNotIn(
            "setPieces", keys,
            "a key ABSENT from the snapshot was reported on. Absent is not zero — it would show "
            "as a catastrophic loss of every set piece he owns.")
        self.assertEqual(r["state"], LH.OK)

    def test_it_never_restores_and_never_fails_a_build(self):
        src = io.open(os.path.join(HERE, "ledger_highwater.py"), encoding="utf-8").read()
        self.assertNotIn("sys.exit(1)", src)
        self.assertNotIn("raise SystemExit(1)", src)
        body = src.split('"""', 2)[-1]
        for verb in ("d2r_foundLog", "localStorage", "setItem"):
            self.assertNotIn(verb, body,
                             "this module appears to touch the live ledger (%s). It REPORTS — "
                             "putting entries back would hide whatever removed them." % verb)


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
