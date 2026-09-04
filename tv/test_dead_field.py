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

    def test_the_store_PATH_is_asked_of_its_owner_never_guessed(self):
        """⚠⚠ REG-540, reproduced before it was believed. The first cut joined
        "reel_tombstones.json" to THIS directory, and the owner does not resolve it that way —
        `reel_retention._tombstone_path(hist)` picks a fixture root, a hist dir, or HERE. Passing a
        hist dir, which is the shape the deleter actually runs in, sends its tombstones to
        `<hist>/reel_tombstones.json` while this read `tv/reel_tombstones.json`. **The detector
        would have watched a file the deletions never reach.** Third instance of this shape in one
        session. [[copy-drift]] §1
        """
        import os
        import reel_retention as RR
        got, why = DF._path_of(DF.WATCHED[0][1])
        self.assertTrue(got, "the store path could not be resolved at all: %r" % why)
        self.assertEqual(
            os.path.abspath(got), os.path.abspath(RR._tombstone_path()),
            "the detector reads a different file than reel_retention says it writes.")

        # ⚠⚠ AND THE EQUALITY ABOVE IS NOT THE GUARD — IT PASSES ON THE DEFECT. Measured: with
        # the hardcoded "reel_tombstones.json" restored, the two still agree, because HERE and the
        # owner's default resolve to the same file TODAY. A guard that only holds while nothing has
        # moved is not measuring the join, it is measuring a coincidence — and this file's own
        # sabotage run caught that: the hardcoded-path sabotage went green here and was only
        # noticed by an unrelated test. So MOVE the owner and require the detector to follow.
        real = RR._tombstone_path
        try:
            RR._tombstone_path = lambda *a, **k: "/tmp/moved_by_the_owner/reel_tombstones.json"
            moved, _ = DF._path_of(DF.WATCHED[0][1])
            self.assertEqual(
                moved, "/tmp/moved_by_the_owner/reel_tombstones.json",
                "the owner moved its store and the detector did NOT follow, so it keeps its own "
                "copy of the path. One rename — or one hist dir, which is the shape the deleter "
                "actually runs in — and it watches a file the deletions never reach.")
        finally:
            RR._tombstone_path = real

    def test_a_missing_resolver_is_named_UNKNOWN_not_guessed(self):
        """⚠ BASELINE: the resolver must be able to fail, or the equality above is two constants
        agreeing with themselves. And a guessed path would read a file that may not be the store
        and report ITS rows as the store's."""
        import reel_retention as RR
        real = RR._tombstone_path
        try:
            del RR._tombstone_path
            got, why = DF._path_of(("reel_retention", "_tombstone_path"))
            self.assertIsNone(got, "an owner with no resolver still yielded a path: %r" % (got,))
            self.assertIn("_tombstone_path", why, "the reason does not name what went: %r" % why)
        finally:
            RR._tombstone_path = real

    def test_a_resolver_that_RAISES_is_UNKNOWN_not_a_crash(self):
        import reel_retention as RR
        real = RR._tombstone_path
        try:
            RR._tombstone_path = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
            got, why = DF._path_of(("reel_retention", "_tombstone_path"))
            self.assertIsNone(got, "a raising resolver still yielded a path: %r" % (got,))
            self.assertIn("boom", why, "the reason drops the error: %r" % why)
            r = DF.state()
            self.assertTrue(r["ok"], "a raising resolver took the whole reading down: %s" % r)
            self.assertEqual(r["state"], "UNKNOWN", r)
        finally:
            RR._tombstone_path = real

    def test_a_row_that_is_not_an_object_is_SKIPPED_and_COUNTED_not_a_crash(self):
        """⚠ Found by the cold cross-family look at v2539: this raised AttributeError on a non-dict
        row. `state()` filters before calling, so the live path was safe — but this function is
        PUBLIC and the guard calls it directly, and **a detector that crashes on malformed data
        goes silent exactly when the data is bad**. Counted, not silently dropped: dropping rows
        would shrink the denominator the floor is measured against."""
        rows = self._rows(39, startedTs=None) + [None]
        r = DF.dead_fields(rows)
        self.assertEqual(r["state"], "DEAD_FIELDS", r)
        self.assertEqual(r["skipped"], 1, "the unjudgeable row was not counted: %s" % r)
        self.assertIn("could not be judged", r["why"],
                      "the report does not say a row was skipped, so the reader takes the "
                      "denominator at face value: %r" % r["why"])

    def test_ZERO_and_FALSE_are_FILLED_not_dead(self):
        """⚠⚠ A COLD REVIEW CLAIMED THE OPPOSITE AND WAS WRONG — it said `0`, `0.0` and `False` are
        treated as not-filled. Measured: all three count as filled 40 of 40, because `0 != ""` and
        `0 != []` are both True in Python. The finding was NOT taken. This pins the real behaviour
        so a future reader does not 'fix' it back to the reviewer's version — `0` is a MEASURED
        value and calling it dead would be the exact zero-vs-None collapse this file is about."""
        for val in (0, 0.0, False):
            r = DF.dead_fields(self._rows(40, z=val))
            self.assertEqual(r["dead"], [],
                             "%r was reported as a dead field. It is a measured value." % (val,))
            self.assertEqual(r["filled"].get("z"), 40, "%r was not counted as filled" % (val,))
        for val in (None, "", []):
            r = DF.dead_fields(self._rows(40, z=val))
            self.assertEqual(r["dead"], ["z"], "%r should read as nothing recorded" % (val,))

    def test_a_WHOLLY_unreadable_store_is_UNKNOWN_not_OK(self):
        """⚠⚠ REG-541, and I shipped it in the fix for the previous instance of this same class.
        Measured on the version that went out: 40 rows, ALL of them non-objects, reported

            state OK · "every field present on all 40 row(s) carries a value somewhere"

        a sentence that is flatly false, from the one module whose whole job is refusing to call
        the unmeasured clean. `n` was the row COUNT while the judging used `on_every`, which stays
        None when nothing was a dict — so `dead` came back empty and empty read as OK.
        """
        r = DF.dead_fields([None] * 40)
        self.assertEqual(r["state"], "UNKNOWN",
                         "a store where not one row could be read reported %r: %s"
                         % (r["state"], r["why"]))
        self.assertEqual(r["judged"], 0, r)
        self.assertNotIn("carries a value somewhere", r["why"],
                         "it still claims every field carries a value, over rows it never read")

    def test_the_FLOOR_counts_rows_that_could_be_JUDGED_not_rows_that_existed(self):
        """⚠ 39 garbage rows and one good one is a 1-row sample wearing a 40-row denominator."""
        r = DF.dead_fields([None] * 39 + [{"a": 1, "b": 2}])
        self.assertEqual(r["state"], "UNKNOWN", r["why"])
        self.assertEqual((r["judged"], r["checked"], r["skipped"]), (1, 40, 39), r)

    def test_the_SKIP_is_named_in_every_branch_not_only_when_something_is_wrong(self):
        """⚠ The first cut appended the skip note only to the DEAD_FIELDS message, so a clean
        verdict over a partly-unreadable store said nothing about the rows it could not read."""
        r = DF.dead_fields(self._rows(39) + [None])          # every field filled -> OK branch
        self.assertEqual(r["state"], "OK", r["why"])
        self.assertIn("could not be judged", r["why"],
                      "a clean verdict hid the skipped row: %r" % r["why"])

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
