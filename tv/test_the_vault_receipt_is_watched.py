# -*- coding: utf-8 -*-
"""A vault row must be able to SHOW why it is there, and the heart must say when it cannot.

Konyo asked for a receipt on a vault item — tooltip-style, the full-HD frame from the reel that
witnessed it — and pushed back when I said nothing was built. He was right. The console carries the
whole apparatus: a cursor-following float on `.rc-art`, a full-HD viewer on the `.rcpt-ic` eye
reading the real on-disk /hist/<frameId>.jpg, and a route-to-source click. The evidence store
already records {reel, frame, lane} per sighting.

What never existed is the INTRODUCTION: the vault emits none of those hooks. Built, correct, joined
to nothing. Nothing watched the join either, which is why it stayed invisible until he remembered
it. [[the-unjoined-end]] [[plumbing-with-no-tap]]

⚠ MEASURED: 172 owned, 153 filed into lockers, ZERO carrying a sighting. A row with no receipt
looks identical to one with a reel behind it — which is how 150 rows from a retired found-ever
backfill sat in his lockers looking exactly like real finds.
"""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

import health_engine as HE  # noqa: E402


def _backup(d, owned, ev, mule):
    p = os.path.join(d, "ledger_2026-01-01_000000.json")
    with io.open(p, "w", encoding="utf-8") as fh:
        fh.write(json.dumps({"allStores": {
            "d2r_owned": json.dumps(owned),
            "d2r_foundEvidence": json.dumps(ev),
            "d2r_muleAssign": json.dumps(mule)}}))
    return p


class TestTheVaultReceiptIsWatched(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.d, True)

    def _pin_the_bank(self):
        """⚠ the second eye on 262e1a56: these two cases are about the BACKUP, but REG-1222 made both
        doors consult the receipt bank too - so on a machine whose bank opens nothing they read WARN
        and go red, on another they pass. Pin the bank to a partial open (UNKNOWN on every machine) so
        the case measures what its name says."""
        real = HE._receipts_resolve
        HE._receipts_resolve = lambda *a, **k: (126, 450)
        self.addCleanup(setattr, HE, "_receipts_resolve", real)

    def test_an_absent_backup_is_UNKNOWN_never_zero(self):
        """'no backup' and 'no receipts' are opposite facts and must never share a row."""
        self._pin_the_bank()
        r = HE.check_vault_receipts(backup_dir=self.d)
        self.assertEqual(r["state"], HE.UNKNOWN,
                         "an empty backup dir reported %r — a count nobody could take must not "
                         "read as a count of zero" % (r["state"],))

    def test_an_unreadable_backup_is_UNKNOWN_never_zero(self):
        with io.open(os.path.join(self.d, "ledger_bad.json"), "w", encoding="utf-8") as fh:
            fh.write("{not json")
        self._pin_the_bank()
        r = HE.check_vault_receipts(backup_dir=self.d)
        self.assertEqual(r["state"], HE.UNKNOWN,
                         "an unreadable backup reported %r instead of UNKNOWN" % (r["state"],))

    def test_an_unreadable_backup_still_says_whether_a_receipt_OPENS(self):
        """Second eye on v3490 (grok-4.7): the corrupt-backup return skipped the resolution v3490
        added for an empty directory, so the row carried no evidence and could never grade WARN."""
        with io.open(os.path.join(self.d, "ledger_bad.json"), "w", encoding="utf-8") as fh:
            fh.write("{not json")
        real = HE._receipts_resolve
        try:
            HE._receipts_resolve = lambda *a, **k: (0, 450)
            r = HE.check_vault_receipts(backup_dir=self.d)
            self.assertEqual(r["state"], HE.WARN, "nothing opens and the row did not say so: %r" % (r,))
            self.assertIn("receiptFrames 0 of 450", " ".join(r.get("evidence") or []))
            HE._receipts_resolve = lambda *a, **k: (126, 450)
            r = HE.check_vault_receipts(backup_dir=self.d)
            self.assertEqual(r["state"], HE.UNKNOWN)
            self.assertIn("receiptFrames 126 of 450", " ".join(r.get("evidence") or []))
        finally:
            HE._receipts_resolve = real

    def test_it_counts_the_rows_that_actually_carry_a_sighting(self):
        _backup(self.d, ["A", "B", "C"],
                {"A": {"sightings": [{"reel": "r1", "frame": "f1.jpg"}]},
                 "B": {"sightings": []}},          # present but EMPTY is not a sighting
                {"A": "uni-weap", "B": "uni-armor"})
        r = HE.check_vault_receipts(backup_dir=self.d)
        # ⚠ evidence is a LIST by contract — `_row` does list(evidence or []), so a dict
        # would land as its key names and every number would vanish. That is exactly what
        # v3145's organ did until v3167.
        e = r.get("evidence") or []
        self.assertIn("owned 3", e, "evidence: %r" % (e,))
        self.assertIn("filed 2", e, "an unfiled row is still owned: %r" % (e,))
        self.assertIn("withSighting 1", e,
                      "an EMPTY sightings list is not a receipt: %r" % (e,))

    def test_it_reports_whether_a_receipt_can_actually_OPEN(self):
        """⚠ v3193 — THE MEASUREMENT, NOT THE BUTTON. The row used to grade only whether the vault
        emitted a receipt HOOK; it did, and the row was green while the hook resolved 4 of 450
        banked frames because it addressed a flat path the frames do not live at. Presence and
        resolution are different questions and only one of them is the feature.

        This asserts the row SAYS which it measured — a count when the bank can be read, and an
        explicit UNKNOWN when it cannot. A silent omission would let the old green come back."""
        r = HE.check_vault_receipts()
        line = r.get("line") or ""
        ev = " ".join(str(x) for x in (r.get("evidence") or []))
        got, tested = HE._receipts_resolve()
        print("   resolve: %d of %d · line mentions frames: %s" % (got, tested, "frame" in line))
        self.assertIn("receiptFrames", ev,
                      "the evidence does not carry the resolution measurement at all, so a "
                      "receipt that opens nothing is indistinguishable from one that opens")
        if tested:
            self.assertIn("banked best-frames", line,
                          "the bank was read (%d of %d) and the row does not say how many "
                          "receipts can actually be opened: %r" % (got, tested, line[:140]))
        else:
            self.assertIn("UNKNOWN", line,
                          "the bank could not be read and the row does not say so — an "
                          "unmeasured resolution must never read as a clean one")

    def test_it_says_when_the_vault_cannot_show_a_receipt_at_all(self):
        """The join is the finding. Counting sightings while the vault emits no hook would report
        a number about evidence that can never reach his screen."""
        _backup(self.d, ["A"], {"A": {"sightings": [{"reel": "r", "frame": "f.jpg"}]}}, {"A": "x"})
        r = HE.check_vault_receipts(backup_dir=self.d)
        # ⚠⚠ v3193 — THIS GUARD HAD STOPPED FIRING AND THE TEST PASSED EXAMINING NOTHING.
        # It keyed on the literal "rc-art=0". v3182 changed _receipt_hooks to count the board's
        # own viewer hooks, so the evidence read "rc-art=None" — never "=0" — the `if` was never
        # true, and BOTH assertions below had not run since. The heart caught it: the red-proof
        # that deletes the sentence stayed GREEN. A law must not decide whether to look by
        # matching a string that another version is free to rename.
        # [[label-outlived-referent]] [[feedback-blind-fixture-green-gate]]
        #
        # Ask the ORGAN's own joined verdict instead of parsing its prose.
        joined = bool((HE._receipt_hooks() or {}).get("ok")) and HE._vault_row_has_frame()
        print("   receipt lane joined: %s" % joined)
        if not joined:
            self.assertIn("NO receipt hook", r["line"],
                          "the vault emits no receipt hook and the row does not say so: %r"
                          % (r["line"][:160],))
            self.assertEqual(r["state"], HE.WARN,
                             "an unjoined receipt lane reported %r" % (r["state"],))
        else:
            # ⚠ AND THE JOINED CASE IS ASSERTED TOO, so this test can never again be a no-op:
            # whichever way the join goes, something is checked.
            self.assertNotIn("NO receipt hook", r["line"],
                             "the lane IS joined and the row still claims it emits no hook")


RED_PROOF = [
    {
        "why": "second eye on v3490 - a corrupt ledger backup returns before the receipt resolution again: no evidence, never WARN",
        "file": "health_engine.py",
        "find": "        return _resolution_only(\"the newest ledger backup could not be read (%s), so the receipt \"\n",
        "replace": "        return _row(\"vaultReceipts\", UNKNOWN, \"unreadable\", k=_atkK, n=_atkN)\n        return _resolution_only(\"the newest ledger backup could not be read (%s), so the receipt \"\n",
        "matches": 1,
    },
    {
        "why": 'v3193 — the old anchor deleted the "NO receipt hook" sentence, which only appears '
               'on the UNJOINED path his tree never takes, so the tamper was invisible. This '
               'deletes the RESOLUTION measurement instead: the organ then reports a sighting '
               'count while saying nothing about whether one frame can actually be opened, which '
               'is the defect v3182 was written to end',
        "file": 'health_engine.py',
        "find": '    _rres = _receipts_resolve()',
        "replace": '    _rres = (0, 0)  # _HEART2_TAMPERED_',
        "matches": 1,
    },
    {'why': "reports an unreadable ledger backup as a clean zero instead of UNKNOWN, so 'nobody could look' and 'nothing is there' become the same row", 'file': 'health_engine.py', 'find': '        return _row("vaultReceipts", WARN if _broken0 else UNKNOWN, why + _clause0,', 'replace': '        return _row("vaultReceipts", WARN if _broken0 else OK, why + _clause0,', 'matches': 1},
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
