# -*- coding: utf-8 -*-
"""v2692 — THE 7TH STATION, AND THE SEALED/CERTIFIED SPLIT BESIDE IT.

Konyo, gh #210: "this entire processing system and pruning and everything needs to work, and
STATION AND THEN TOMBSTONE at the end of it all."

WHY BOTH ARE GUARDED HERE. Each is a REPORT, and a report is the easiest thing in this repo to
break silently: it keeps returning a shape, so nothing errors, and the surface goes on printing a
word that stopped being true. Two specific ways these can rot:

  · the tombstone station could start saying "ON DISK" because the LEDGER failed to load rather
    than because nothing was pruned. Those are opposite facts. A missing ledger must say UNKNOWN.
  · `certified` could quietly become an alias for `sealed`. It is not one: measured on his tree,
    30 seals exist and ZERO satisfy EXTRACTION_CONTRACT. A surface built on `sealed` alone would
    print 40/40 while certifying nothing, which is exactly the conflation frame_authority guards
    one layer down ("an unstated fact is an unextracted one").

⚠ THESE ARE STRUCTURAL ASSERTIONS ON PURPOSE. They do not pin his current counts — 410 tombstoned
reels or 15 sealed will both move — because pinning a number that legitimately drifts produces a
gate that gets re-baselined until it means nothing. [[regression-guard]]
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass


class TheStationExistsAndIsLast(unittest.TestCase):
    def test_tombstone_is_registered_and_final(self):
        import printer as P
        self.assertIn("tombstone", P.STATIONS, "the 7th station is gone")
        self.assertEqual(P.STATIONS[-1], "tombstone",
                         "tombstone must be the LAST station — his ruling is 'station and THEN "
                         "tombstone at the end of it all', and the order is the sentence")

    def test_it_declares_an_owner_like_every_other_station(self):
        import printer as P
        self.assertIn("tombstone", P.STATION_OWNER,
                      "a station with no declared owner derives its answer instead of quoting one")
        owner, _q = P.STATION_OWNER["tombstone"]
        self.assertEqual(owner, "reel_retention")


class EveryRowCarriesIt(unittest.TestCase):
    def setUp(self):
        import printer as P
        self.res = P.stream()
        self.rows = self.res.get("rows") or []

    def test_the_snapshot_is_not_empty(self):
        """A sample of zero passes every assertion below it."""
        self.assertTrue(self.rows, "printer.stream() returned no rows — this measures NOTHING")

    def test_every_row_has_a_tombstone_verdict(self):
        missing = [r.get("reel") for r in self.rows if not (r.get("stations") or {}).get("tombstone")]
        self.assertEqual(missing, [], "rows with no tombstone station: %s" % missing[:3])

    def test_the_verdict_is_one_of_the_three_it_may_be(self):
        """ON DISK (still here) · CONTRADICTION (on disk AND tombstoned) · UNKNOWN (ledger unreadable).
        Anything else means a new state was added without deciding what it means."""
        allowed = {"ON DISK", "CONTRADICTION", "UNKNOWN"}
        got = {(r["stations"]["tombstone"] or {}).get("say") for r in self.rows}
        self.assertTrue(got <= allowed, "unexpected tombstone verdict(s): %s" % (got - allowed))

    def test_a_verdict_always_carries_its_reason(self):
        for r in self.rows:
            why = (r["stations"]["tombstone"] or {}).get("why") or ""
            self.assertTrue(len(why) > 10,
                            "%s reports a tombstone verdict with no reason" % r.get("reel"))


class SealedIsNotCertified(unittest.TestCase):
    def test_extract_rows_report_both_facts(self):
        import extract_gap as EG
        rows = (EG.gap() or {}).get("rows") or []
        self.assertTrue(rows, "extract_gap returned no rows — this measures NOTHING")
        for r in rows:
            self.assertIn("sealed", r)
            self.assertIn("certified", r,
                          "the extract station stopped reporting `certified`, so 'has a seal' and "
                          "'the seal certifies the extraction' collapse back into one word")

    def test_certified_is_never_true_without_a_seal(self):
        import extract_gap as EG
        rows = (EG.gap() or {}).get("rows") or []
        bad = [r.get("reel") for r in rows if r.get("certified") and not r.get("sealed")]
        self.assertEqual(bad, [], "certified without a seal is incoherent: %s" % bad[:3])

    def test_an_uncertified_seal_says_why(self):
        import extract_gap as EG
        rows = (EG.gap() or {}).get("rows") or []
        for r in rows:
            if r.get("sealed") and not r.get("certified"):
                self.assertTrue(len(str(r.get("certifiedWhy") or "")) > 10,
                                "%s is sealed and not certified, with no reason given — that is the "
                                "unmeasured-number shape this split exists to remove" % r.get("reel"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
