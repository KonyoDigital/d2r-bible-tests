# -*- coding: utf-8 -*-
"""A15 clause 1 — ONE START POINT, and the two ways a probe like this lies.

⚠⚠ THE FIRST LIE IS A SOURCE GREP. A7 tried to count writers twice — a filename-adjacency grep,
then an AST walk resolving path constants — and BOTH returned zero for all four stores, because
both were measuring my own instrument's reach rather than the codebase. So this clause is put to
the ARTIFACT: forty reels that already exist, each carrying the record its maker wrote.

⚠⚠ THE SECOND LIE IS CRYING WOLF. Three modules can write a reel's index.json, and only one of them
is a FRONT DOOR: `reel_index` restores an index a reel already had (and refuses to rewrite one that
parses), `vault_fixture_reels` writes a tree it is handed. A probe that reports three doors reports
a violation on a healthy shelf, and a row that cries wolf is a row he learns to skip — the exact
defect CF-10 records three instances of.

So: a repair is not a violation, a FIXTURE REEL ON HIS LIVE SHELF IS, and an index nobody can
attribute stays UNKNOWN rather than being rounded to the common case.
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import one_start_point as OSP   # noqa: E402


class OneStartPointIsAskedOfTheShelf(unittest.TestCase):

    def _shelf(self, reels):
        """Build a throwaway shelf. -> path (cleaned up automatically).

        ⚠ It is built under tempfile and NEVER under his frames tree — a fixture that writes to the
        live shelf is the defect this very probe exists to detect. [[fixtures-never-touch-live-data]]
        """
        d = tempfile.mkdtemp(prefix="osp_")
        self.addCleanup(shutil.rmtree, d, True)
        for name, idx in reels.items():
            rd = os.path.join(d, name)
            os.makedirs(rd)
            if idx is not None:
                with open(os.path.join(rd, "index.json"), "w") as fh:
                    fh.write(idx if isinstance(idx, str) else json.dumps(idx))
        return d

    def _rec(self, **extra):
        r = {"sessionId": "s_1", "n": 3, "frames": [{"f": "a.jpg", "ts": 1}]}
        r.update(extra)
        return r

    def test_a_shelf_of_recorder_reels_is_ONE_DOOR(self):
        r = OSP.start_points(self._shelf({"reel_s_1": self._rec(), "reel_s_2": self._rec()}))
        self.assertEqual(r["state"], "ONE_DOOR", r["why"])
        self.assertEqual(r["counts"].get("recorder"), 2, r["counts"])

    def test_a_REPAIRED_reel_is_not_counted_as_a_second_front_door(self):
        """⚠ `reel_index` restores an index a reel already had. Counting that as a violation would
        report a defect on his real shelf, where 2 of 40 reels are repairs."""
        r = OSP.start_points(self._shelf({"reel_s_1": self._rec(),
                                          "reel_s_2": self._rec(rebuilt=True)}))
        self.assertEqual(r["counts"].get("repair"), 1,
                         "the repair door was not recognised at all: %s" % r["counts"])
        self.assertEqual(
            r["state"], "ONE_DOOR",
            "a repaired index was counted as a second front door. reel_index does not mint a reel "
            "from footage — it rebuilds an index the reel already had, and refuses to rewrite one "
            "that parses. On his shelf that would report MULTIPLE_DOORS on a healthy tree, and a "
            "row that cries wolf is a row he learns to skip. %s" % r["why"])

    def test_a_FIXTURE_reel_on_the_live_shelf_IS_a_second_door(self):
        """⚠ BASELINE for the test above — if nothing could ever reach MULTIPLE_DOORS, calling a
        repair 'not a violation' would be describing a function that can never object."""
        r = OSP.start_points(self._shelf({"reel_s_1": self._rec(),
                                          "reel_s_2": {"reel": "reel_s_2", "frames": [],
                                                       "synthetic": True}}))
        self.assertEqual(r["counts"].get("fixture"), 1,
                         "a synthetic reel on the live shelf was not recognised: %s" % r["counts"])
        self.assertEqual(
            r["state"], "MULTIPLE_DOORS",
            "footage this pipeline never recorded is sitting on the shelf wearing a reel's "
            "clothes, and the probe called it one start point: %s" % r["why"])

    def test_the_fixture_door_is_caught_by_its_SHAPE_when_the_mark_is_gone(self):
        """One word a future edit could drop must not be the only tell. Keys on `reel`, not
        `sessionId` — the fixture builder's other signature."""
        r = OSP.start_points(self._shelf({"reel_s_2": {"reel": "reel_s_2", "frames": []}}))
        self.assertEqual(r["counts"].get("fixture"), 1,
                         "with `synthetic` removed the fixture record was not recognised by its "
                         "shape either: %s" % r["counts"])

    def test_an_unattributable_index_stays_UNKNOWN_not_rounded_to_the_recorder(self):
        """⚠ The common case is a recorder reel, and defaulting to it would be the
        default-as-measurement defect. [[unknown-stays-unknown]]"""
        r = OSP.start_points(self._shelf({"reel_s_9": {"frames": []}}))     # no sessionId, no n
        self.assertEqual(r["counts"].get("UNKNOWN"), 1,
                         "an index carrying neither the core nor a mark was attributed anyway: %s"
                         % r["counts"])
        self.assertEqual(r["state"], "MULTIPLE_DOORS",
                         "a reel nobody can attribute was folded into 'one door': %s" % r["why"])

    def test_the_CORE_is_a_SHAPE_not_a_set_of_key_names(self):
        """⚠⚠ REG-535, found by a COLD cross-family review of v2533 and reproduced before believed.

        The first cut asked only `k not in idx`, so `{"sessionId": "x", "n": 3, "frames": None}`
        was attributed to THE RECORDER — `frames` as 0, as "98" and as None all returned
        "recorder". Nothing that mints a reel writes any of those, so a broken index read as a
        healthy birth record and the shelf still said ONE_DOOR. Key presence standing in for a
        measurement is [[unknown-stays-unknown]] wearing a dict.

        ⚠ It changed NOTHING on his shelf — still 38 recorder / 2 repair / ONE_DOOR — so this is
        insurance, not a live correction, and saying otherwise would be inventing a fix.
        """
        for bad, tell in ((0, "frames is int"), ("98", "frames is str"), (None, "frames is None")):
            door, why = OSP._door_of({"sessionId": "s_1", "n": 3, "frames": bad})
            self.assertEqual(
                door, "UNKNOWN",
                "an index whose `frames` is %r was attributed to the recorder. The key is there "
                "and the SHAPE is not, and nothing that mints a reel writes that." % (bad,))
            self.assertIn(tell, why, "the reason does not name what is wrong: %r" % why)
        self.assertEqual(OSP._door_of({"sessionId": "", "n": 3, "frames": []})[0], "UNKNOWN",
                         "an empty sessionId passed as a birth record")
        self.assertEqual(OSP._door_of({"sessionId": "s", "n": "3", "frames": []})[0], "UNKNOWN",
                         "a string frame count passed as a number")

    def test_a_BOOLEAN_frame_count_is_not_a_number(self):
        """⚠ `isinstance(True, int)` is True in Python, so a bare int check lets `n: true` through
        as a frame count. The classic trap, pinned rather than left to a reader."""
        self.assertEqual(OSP._door_of({"sessionId": "s", "n": True, "frames": []})[0], "UNKNOWN",
                         "`n: True` was accepted as a frame count")

    def test_BASELINE_a_well_shaped_core_still_reads_as_the_recorder(self):
        """⚠ Or the shape check is refusing everything and ONE_DOOR became unreachable."""
        self.assertEqual(
            OSP._door_of({"sessionId": "s_1", "n": 3, "frames": [{"f": "a.jpg", "ts": 1}]})[0],
            "recorder",
            "the shape check now refuses a healthy record, so nothing can ever be attributed")

    def test_a_reel_with_no_index_is_reported_not_skipped(self):
        r = OSP.start_points(self._shelf({"reel_s_5": None}))
        self.assertEqual([x["door"] for x in r["rows"]], ["UNKNOWN"],
                         "a reel whose birth is unrecorded was silently skipped: %s" % r["rows"])

    def test_an_EMPTY_shelf_is_UNKNOWN_not_a_clean_bill(self):
        r = OSP.start_points(self._shelf({}))
        self.assertEqual(r["state"], "UNKNOWN", r["why"])
        self.assertFalse(r["ok"], "an empty shelf answered ok=True, so nothing-to-read reads as "
                                  "a passing measurement: %s" % r["why"])

    def test_a_MISSING_shelf_says_UNKNOWN_not_zero_doors(self):
        r = OSP.start_points(os.path.join(tempfile.gettempdir(), "osp_no_such_dir_ever"))
        self.assertEqual(r["state"], "UNKNOWN", r["why"])
        self.assertIn("UNKNOWN", r["why"])


if __name__ == "__main__":
    # ⚠ HIS WINDOWS PC PRINTS STDOUT AS cp1255, AND EVERY ⚠ IN THIS FILE IS UNPRINTABLE THERE.
    # Without this the suite crashes while REPORTING — a clean tree exits non-zero and the failure
    # is in the messenger, not the subject. tv/test_control.py asserts every non-ASCII CLI enables
    # it, and it caught these two at the gate.
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
