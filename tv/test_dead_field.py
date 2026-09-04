# -*- coding: utf-8 -*-
"""A field recorded on every row and filled on none — and why the console has to be the one asking.

⚠⚠ WHAT WAS NOT CAUGHT. `reel_retention._tombstone` recorded each deleted reel's `startedTs` from
two keys **no reel index has ever carried** (0 of 40, measured). It wrote `None` **410 times out of
410**, on the one door with no undo, and nothing said so. It was found by READING A LINE — a
detector that fires once, against a field that had been dead for 410 deletions.

His instruction: *"connect it to the heart of the console that way we would have caught it"*.

These pin the two ways this detector would lie:
  · reporting a young store as clean — a zero over rows that cannot disagree measures the SAMPLE;
  · reporting a sometimes-null field as dead — that is a field with sometimes nothing to say, and
    a row that cries wolf is a row he learns to skip.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import dead_field as DF   # noqa: E402


class AFieldFilledOnNoRowIsNotAField(unittest.TestCase):

    def _rows(self, n, **fixed):
        out = []
        for i in range(n):
            r = {"reel": "reel_%d" % i, "deletedTs": 1787000000000 + i}
            r.update(fixed)
            out.append(r)
        return out

    def test_it_catches_the_field_that_is_never_filled(self):
        r = DF.dead_fields(self._rows(410, startedTs=None))
        self.assertEqual(r["state"], "DEAD_FIELDS", r["why"])
        self.assertEqual(r["dead"], ["startedTs"], r)

    def test_ONE_filled_row_is_enough_to_clear_it(self):
        """⚠ It reports a field that has NEVER carried a value. Once the fix lands and one real
        deletion fills it, the store stops being reported — the historical nulls do not keep it lit
        forever, because the question is *does this field ever work*, not *is it always set*."""
        rows = self._rows(410, startedTs=None)
        rows[-1]["startedTs"] = 1784984130673
        r = DF.dead_fields(rows)
        self.assertEqual(r["state"], "OK", r["why"])
        self.assertEqual(r["dead"], [])

    def test_a_SOMETIMES_null_field_is_never_reported(self):
        """⚠ `focus` is legitimately null on a reel with no declared focus. Calling that dead is
        crying wolf, and a row that cries wolf is a row he learns to skip."""
        rows = self._rows(200, focus=None) + self._rows(210, focus="chronicle-uniques")
        r = DF.dead_fields(rows)
        self.assertEqual(r["dead"], [], "a sometimes-null field was reported as dead: %s" % r)

    def test_a_field_missing_from_SOME_rows_is_not_judged(self):
        """A field must be on EVERY row to be 'meant to be there'. A key only some rows carry is a
        shape difference, which is a different finding and not this one's."""
        rows = self._rows(300, ghost=None) + self._rows(200)
        r = DF.dead_fields(rows)
        self.assertNotIn("ghost", r["dead"],
                         "a field absent from 200 rows was judged as if declared on all: %s" % r)

    def test_a_YOUNG_store_is_UNKNOWN_not_clean(self):
        """⚠⚠ THE FLOOR IS THE WHOLE DESIGN. A zero over rows that cannot disagree measures the
        SAMPLE — the mistake A15 clause 1 exists to avoid."""
        r = DF.dead_fields(self._rows(3, startedTs=None))
        self.assertEqual(r["state"], "UNKNOWN", r["why"])
        self.assertEqual(r["dead"], [], "a 3-row store was judged: %s" % r)
        self.assertIn("floor", r["why"])

    def test_BASELINE_the_floor_can_be_crossed(self):
        """⚠ Or every store is UNKNOWN forever and the detector is decorative."""
        r = DF.dead_fields(self._rows(DF.MIN_ROWS, startedTs=None))
        self.assertEqual(r["state"], "DEAD_FIELDS",
                         "exactly at the floor nothing was judged, so the floor is unreachable")

    def test_an_UNREADABLE_store_is_UNKNOWN_not_OK(self):
        r = DF.dead_fields(None)
        self.assertEqual(r["state"], "UNKNOWN", r["why"])
        self.assertEqual(r["checked"], 0)

    def test_it_reports_and_refuses_nothing(self):
        """Nothing here fails a build or blocks a button — it is EVIDENCE, like CF-13's reach."""
        r = DF.state()
        self.assertTrue(r["ok"], "the reading refused: %s" % r)
        self.assertIn("state", r)


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
