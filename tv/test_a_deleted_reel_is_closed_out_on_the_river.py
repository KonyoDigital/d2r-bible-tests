# -*- coding: utf-8 -*-
"""REG-1615 — A REEL THE SHELF NO LONGER HAS IS CLOSED OUT ON THE RIVER, AND THE HEART NAMES ONE NOBODY LOGGED.

His fleet card read "river stuck" on every PC (2026-09-30). On his Mac the stamp log still placed 64 reels on the
river that had left the shelf: every one closed out by the retention pass (its closure ledger) or reaped by the
recorder's disk floor (its reap log), and neither deleter had ever stamped the log - river_stamp's own docstring
promised a TOMBSTONE writer "inside the deleter" that did not exist (the w26 audit: 0 TOMBSTONE rows against 47
ROUTED). REG-1614 stopped the fleet census counting them; this joins the end and hands the class to the heart:
  1. river_stamp.close_out stamps TOMBSTONE (an OBSERVER row, the deleter's record in its why) for a reel whose folder
     is gone AND a deleter's own record names - once; never a reel still on the shelf, never one with no record.
  2. a reel gone with NO record is returned, never stamped - a deletion nobody logged - and the corroborator's
     invariant `river-log-matches-the-shelf` goes red on it (it reads DRY: the corroborator never writes).
  3. an unreadable record, store or shelf is UNKNOWN, never a count.
  4. the triage tick closes out AFTER its walk (act, observe, close out), and still never touches the deleter.
Driven over a throwaway world (a temp shelf, ledger, closure ledger and reap log at the paths their OWN writers
resolve); his tree is never read. RED_PROOF below. [[the-unjoined-end]] [[heart-first]] [[unknown-stays-unknown]]
"""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import river_stamp as RS  # noqa: E402
import reel_retention as RR  # noqa: E402
import tv_diablo as TVD  # noqa: E402

RED_PROOF = [
    {
        "why": "REG-1615 - a reel still on the shelf is closed out: the folder check is gone",
        "file": "river_stamp.py",
        "find": "                  if r.get(\"station\") != \"TOMBSTONE\" and not os.path.isdir(os.path.join(hist, reel)))\n",
        "replace": "                  if r.get(\"station\") != \"TOMBSTONE\")\n",
        "matches": 1,
    },
    {
        "why": "REG-1615 - a reel gone with NO deleter record is stamped anyway: the heart can never name it",
        "file": "river_stamp.py",
        "find": "            if why is None:\n                out[\"unrecorded\"].append(reel)\n            elif dry:\n",
        "replace": "            if why is None:\n                why = \"unrecorded\"\n            if dry:\n",
        "matches": 1,
    },
    {
        "why": "REG-1615 - the reap log is never read: the disk floor's deletions stay 'on the river' for ever",
        "file": "river_stamp.py",
        "find": "                    if isinstance(r, dict) and r.get(\"removed\") is True and r.get(\"reel\"):\n",
        "replace": "                    if False:\n",
        "matches": 1,
    },
    {
        "why": "REG-1615 - the corroborator counts an unreadable record as zero instead of UNKNOWN",
        "file": "corroborate.py",
        "find": "        if not r.get(\"ok\") or r.get(\"unread\"):\n            return None\n        return len(r.get(\"unrecorded\") or [])\n",
        "replace": "        return len(r.get(\"unrecorded\") or [])\n",
        "matches": 1,
    },
    {
        "why": "REG-1615 - the triage tick stops closing out: the log keeps every deleted reel on the river again",
        "file": "control_app.py",
        "find": "                _co = _rvs.close_out(\"loop:tvd-retro-triage\", HIST_DIR)\n",
        "replace": "                _co = {}\n",
        "matches": 1,
    },
]


def _row(reel, station, seq, at=1790000000000):
    return {"at": at + seq, "seq": seq, "reel": reel, "station": station, "from": None, "by": "law", "byKind": "observer"}


class _World(unittest.TestCase):
    """A temp shelf with one reel on it, a stamp log naming five, and each deleter's record at the path ITS writer
    resolves for this shelf - asserted to be inside the temp world, never his tree."""

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="close_out_")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.hist = os.path.join(self.d, "frames", "hist")
        os.makedirs(os.path.join(self.hist, "reel_s_1_on"))
        self.led = os.path.join(self.d, "river_stamp.jsonl")
        with io.open(self.led, "w", encoding="utf-8") as fh:
            for i, (reel, st) in enumerate((("reel_s_1_on", "JOIN"), ("reel_s_2_closed", "ROUTED"),
                                            ("reel_s_3_reaped", "EMPTY"), ("reel_s_4_nobody", "JOIN"),
                                            ("reel_s_5_done", "TOMBSTONE"))):
                fh.write(json.dumps(_row(reel, st, i + 1)) + "\n")
        self.closure = RR._tombstone_path(self.hist)
        self.reaps = TVD._reap_log_path(self.hist)
        for p in (self.closure, self.reaps):
            self.assertTrue(os.path.realpath(p).startswith(os.path.realpath(self.d)),
                            "PREMISE: a deleter's record resolved OUTSIDE the temp world: %s" % p)
        with io.open(self.closure, "w", encoding="utf-8") as fh:
            json.dump({"reels": {"a": {"session": "s_2_closed", "deletedTs": 1790000100000, "why": "sealed"}}}, fh)
        with io.open(self.reaps, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": 1790000200000, "reel": "reel_s_3_reaped", "removed": True,
                                 "by": "recorder-disk-floor"}) + "\n")
            fh.write(json.dumps({"ts": 1790000300000, "reel": "reel_s_4_nobody", "removed": False,
                                 "by": "recorder-disk-floor"}) + "\n")


class ARecordedDeletionIsClosedOut(_World):

    def test_a_recorded_deletion_is_closed_out_once_and_an_unrecorded_one_is_named(self):
        r = RS.close_out("law", self.hist, path=self.led)
        self.assertTrue(r["ok"], r)
        self.assertEqual(sorted(r["closed"]), ["reel_s_2_closed", "reel_s_3_reaped"], r)
        self.assertEqual(r["unrecorded"], ["reel_s_4_nobody"], "a reel gone with no record was not named (a reap row "
                                                               "that did NOT remove it is not a record of removal)")
        rep = RS.index(RS.rows(self.led))
        for reel, word in (("reel_s_2_closed", "closure ledger"), ("reel_s_3_reaped", "reap log")):
            last = rep["byReel"][reel][-1]
            self.assertEqual((last["station"], last["byKind"]), ("TOMBSTONE", "observer"), last)
            self.assertIn(word, last["why"], "the close-out does not say whose record it acted on")
        self.assertEqual(rep["byReel"]["reel_s_1_on"][-1]["station"], "JOIN", "a reel still on the shelf was closed out")
        self.assertEqual(rep["byReel"]["reel_s_4_nobody"][-1]["station"], "JOIN", "an unrecorded reel was stamped")
        again = RS.close_out("law", self.hist, path=self.led)
        self.assertEqual(again["closed"], [], "a second pass wrote again - the close-out is not once")

    def test_dry_classifies_and_writes_nothing(self):
        with io.open(self.led, "rb") as fh:
            before = fh.read()
        r = RS.close_out("law", self.hist, path=self.led, dry=True)
        self.assertEqual(sorted(r["wouldClose"]), ["reel_s_2_closed", "reel_s_3_reaped"])
        self.assertEqual(r["closed"], [])
        with io.open(self.led, "rb") as fh:
            self.assertEqual(fh.read(), before, "a DRY close-out wrote to the log - the corroborator would be writing")

    def test_an_unreadable_record_or_shelf_is_unknown(self):
        with io.open(self.closure, "w", encoding="utf-8") as fh:
            fh.write("{ not json")
        r = RS.close_out("law", self.hist, path=self.led, dry=True)
        self.assertTrue(r["unread"], "a closure ledger that would not read was read as 'nothing was deleted'")
        gone = RS.close_out("law", os.path.join(self.d, "no_shelf"), path=self.led)
        self.assertFalse(gone["ok"], "a shelf that is not there read as a river with nothing gone")


class TheHeartNamesADeletionNobodyLogged(_World):

    def _heart(self):
        import corroborate as C
        with mock.patch.dict(os.environ, {"TV_HIST": self.hist}):
            p = RS._store_path()
            self.assertTrue(os.path.realpath(p).startswith(os.path.realpath(self.d)),
                            "PREMISE: the corroborator's log resolved outside the temp world: %s" % p)
            shutil.copyfile(self.led, p)
            return C.check_one(C._inv_the_river_log_places_only_reels_the_shelf_has_or_a_deleter_recorded)

    def test_an_unlogged_deletion_is_red_and_a_logged_world_agrees(self):
        import corroborate as C
        row = self._heart()
        self.assertEqual(row["state"], C.DISAGREE, "the heart did not name a reel gone with no record: %r" % row)
        self.assertIn("1", row["say"])
        with io.open(self.reaps, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": 1790000400000, "reel": "reel_s_4_nobody", "removed": True,
                                 "by": "recorder-disk-floor"}) + "\n")
        self.assertEqual(self._heart()["state"], C.AGREE, "every deletion logged, and the heart still disagrees")

    def test_an_unreadable_record_is_unknown_not_agreement(self):
        import corroborate as C
        with io.open(self.closure, "w", encoding="utf-8") as fh:
            fh.write("{ not json")
        self.assertEqual(self._heart()["state"], C.UNKNOWN, "an unreadable closure ledger read as a count")

    def test_the_invariant_is_registered(self):
        """run() and the eagle evaluate BUILDERS only - an invariant outside it is graded and never run (its own
        refusal is driven above, on a real world, not by prove_each over his tree)"""
        import corroborate as C
        self.assertIn(C._inv_the_river_log_places_only_reels_the_shelf_has_or_a_deleter_recorded, C.BUILDERS)


class TheTriageTickClosesOut(unittest.TestCase):
    """The loop runs for ever, so its ORDER is read from its code (comments stripped), the way
    test_the_river_has_a_driver reads the lane-before-walk order; close_out itself is driven above."""

    def test_the_tick_closes_out_after_its_walk(self):
        import test_the_river_has_a_driver as D
        body = D._loop_body()
        walk, close = body.find("_rvs.run("), body.find("_rvs.close_out(")
        self.assertGreater(walk, 0, "the river walk is gone from the triage loop")
        self.assertGreater(close, 0, "the triage loop never closes out - every deleted reel stays on the river")
        self.assertLess(walk, close, "the close-out runs before the walk observes")


if __name__ == "__main__":
    unittest.main(verbosity=2)
