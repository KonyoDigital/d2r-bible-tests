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

    def test_an_absent_backup_is_UNKNOWN_never_zero(self):
        """'no backup' and 'no receipts' are opposite facts and must never share a row."""
        r = HE.check_vault_receipts(backup_dir=self.d)
        self.assertEqual(r["state"], HE.UNKNOWN,
                         "an empty backup dir reported %r — a count nobody could take must not "
                         "read as a count of zero" % (r["state"],))

    def test_an_unreadable_backup_is_UNKNOWN_never_zero(self):
        with io.open(os.path.join(self.d, "ledger_bad.json"), "w", encoding="utf-8") as fh:
            fh.write("{not json")
        r = HE.check_vault_receipts(backup_dir=self.d)
        self.assertEqual(r["state"], HE.UNKNOWN,
                         "an unreadable backup reported %r instead of UNKNOWN" % (r["state"],))

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

    def test_it_says_when_the_vault_cannot_show_a_receipt_at_all(self):
        """The join is the finding. Counting sightings while the vault emits no hook would report
        a number about evidence that can never reach his screen."""
        _backup(self.d, ["A"], {"A": {"sightings": [{"reel": "r", "frame": "f.jpg"}]}}, {"A": "x"})
        r = HE.check_vault_receipts(backup_dir=self.d)
        hooks = [x for x in (r.get("evidence") or []) if str(x).startswith("hooks ")]
        if "rc-art=0" in (hooks[0] if hooks else ""):
            self.assertIn("NO receipt hook", r["line"],
                          "the vault emits no receipt hook and the row does not say so: %r"
                          % (r["line"][:160],))
            self.assertEqual(r["state"], HE.WARN,
                             "an unjoined receipt lane reported %r" % (r["state"],))


RED_PROOF = [
    {
        "why": "drops the sentence that says the vault emits no receipt hook, so the organ reports "
               "a sighting count about evidence that can never reach his screen and the unjoined "
               "lane reads as healthy",
        "file": "health_engine.py",
        "find": '        _line += ("; and the vault emits NO receipt hook at all, so even a row that HAS a frame "',
        "replace": '        _line += ("; ok "',
        "matches": 1,
    },
    {
        "why": "reports an unreadable ledger backup as a clean zero instead of UNKNOWN, so 'nobody "
               "could look' and 'nothing is there' become the same row",
        "file": "health_engine.py",
        "find": '        return _row("vaultReceipts", UNKNOWN,\n                    "the newest ledger backup could not be read (%s), so the receipt count is "',
        "replace": '        return _row("vaultReceipts", OK,\n                    "the newest ledger backup could not be read (%s), so the receipt count is "',
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
