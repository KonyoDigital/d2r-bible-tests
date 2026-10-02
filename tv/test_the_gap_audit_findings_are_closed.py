# -*- coding: utf-8 -*-
"""REG-1731 — THE 09-29 GAP AUDIT'S STILL-OPEN FINDINGS, RE-VERIFIED ON 10-02 AND CLOSED (#86).

Each was driven on 09-29 and re-read against the code on 10-02 (ledger: ~/d2r_session_carry/gap_audit/).

  · #17/#32 - the doctor's self_prove row read OK whenever the lane's key was "off" (TV_SELF_PROVE=0), even over a census
    that was missing or stale - nothing will ever prove that PC, so every lock it governs stays shut for good. Off over
    a census that is not current WARNS now and says so. (The row's verdict is one pure function, driven here.)
  · #3/#7 - the HEART's instrument census said WATCHED from the file's proved count, whatever the gate set had become:
    MEASURED on his Mac 10-02, census STALE ("the gates changed since this PC last proved them", 31 owed) and the heart
    said WATCHED. It reads the self-prove lane's last word (free; recomputing costs 1 s on the Mac) and says UNKNOWN,
    with that reason, unless the lane says "current". Not asked yet = unchanged.
RED_PROOF below. [[unknown-stays-unknown]] [[stale-reading]]
"""
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

import control_app as ca  # noqa: E402
import heart2 as h2  # noqa: E402


class TheSelfProveRowWarnsWhenNothingWillProveThisPC(unittest.TestCase):

    def test_off_over_a_missing_census_warns_and_says_why(self):
        ok, line = ca._self_prove_row({"key": "off", "census": "missing", "say": "the self-prove lane is off"})
        self.assertFalse(ok, "the lane is off and the census is missing - every lock stays shut - and the row said OK")
        self.assertIn("lane is OFF", line)

    def test_off_over_a_stale_census_warns(self):
        self.assertFalse(ca._self_prove_row({"key": "off", "census": "stale"})[0])

    def test_premise_off_over_a_current_census_is_still_ok(self):
        self.assertTrue(ca._self_prove_row({"key": "off", "census": "current"})[0])

    def test_premise_a_working_lane_is_ok(self):
        self.assertTrue(ca._self_prove_row({"key": "current", "census": "current"})[0])
        self.assertTrue(ca._self_prove_row({"key": None})[0], "a lane not asked yet must not warn at boot")


class TheHeartSaysWatchedOnlyOverACurrentCensus(unittest.TestCase):

    def setUp(self):
        d = tempfile.mkdtemp(prefix="h2_census_")
        self.addCleanup(shutil.rmtree, d, True)
        p = os.path.join(d, ".heart2.json")
        with open(p, "w") as fh:
            json.dump({"proved": 700, "unproven": 20, "blind": [], "declared": 720, "verdictAt": {}}, fh)
        for patch in (mock.patch.object(h2, "STATE", p),):
            patch.start()
            self.addCleanup(patch.stop)
        saved = dict(ca._SELF_PROVE)
        self.addCleanup(lambda: (ca._SELF_PROVE.clear(), ca._SELF_PROVE.update(saved)))

    def _with_lane(self, census, say=""):
        ca._SELF_PROVE.update(census=census, say=say)
        return ca._heart2_census()

    def test_a_stale_census_is_not_watched(self):
        got = self._with_lane("stale", "the gates changed since this PC last proved them")
        self.assertEqual(got["state"], "UNKNOWN", "a STALE census was reported WATCHED: %r" % (got,))
        self.assertIn("stale", got["why"])

    def test_premise_a_current_census_is_watched(self):
        self.assertEqual(self._with_lane("current")["state"], "WATCHED")

    def test_premise_a_lane_not_asked_yet_changes_nothing(self):
        self.assertEqual(self._with_lane(None)["state"], "WATCHED")



class AnUnreadableShelfIsNotAnIndexedShelf(unittest.TestCase):
    """REG-1732 (#86 item 23) - listdir failing returned [] and the doctor said "every reel has an index"."""

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="shelf_idx_")
        self.addCleanup(shutil.rmtree, self.d, True)

    def test_a_shelf_that_does_not_exist_yet_is_a_measured_empty(self):
        self.assertEqual(ca._reels_missing_index(os.path.join(self.d, "never_filmed")), [])

    def test_premise_a_reel_with_frames_and_no_index_is_listed(self):
        r = os.path.join(self.d, "reel_s_1_1")
        os.makedirs(r)
        open(os.path.join(r, "f_0001.jpg"), "wb").close()
        got = ca._reels_missing_index(self.d)
        self.assertEqual([n for n, _c in (got or [])], ["reel_s_1_1"], got)

    def test_a_shelf_that_cannot_be_read_is_unknown(self):
        # REG-1736 - ON EVERY OS. This case used chmod 000 and was skipped on Windows (chmod does not refuse a listdir
        # there), so on the ALT its red-proof stayed green and the law read BLIND - REG-1724's mistake, repeated the
        # same day. A listdir that raises is the same code path on every OS.
        def _refuse(path):
            raise PermissionError(13, "Permission denied", path)
        with mock.patch.object(ca.os, "listdir", _refuse):
            got = ca._reels_missing_index(self.d)
        self.assertIsNone(got, "an unreadable shelf read as 'no reel lacks its index'")


RED_PROOF = [
    {"why": "REG-1731 - the self_prove row reads OK again with the lane off over a census nobody will prove",
     "file": "control_app.py",
     "find": "    _sp_shut = _sp_key == \"off\" and _sp_census != \"current\"\n",
     "replace": "    _sp_shut = False\n",
     "matches": 1},
    {"why": "REG-1731 - the heart says WATCHED again over a stale census",
     "file": "control_app.py",
     "find": "        if _h2_state == \"WATCHED\" and ((_h2_lane and _h2_lane != \"current\") or (_h2_off and _h2_lane != \"current\")):\n",
     "replace": "        if False:\n",
     "matches": 1},
    {"why": "REG-1732 - an unreadable shelf reads as every reel indexed again",
     "file": "control_app.py",
     "find": "        names = sorted(os.listdir(hist))\n    except Exception:\n        return None\n",
     "replace": "        names = sorted(os.listdir(hist))\n    except Exception:\n        return out\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
