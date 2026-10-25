#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""THE HIST SIZE CAP (Elad 2026-10-24: "cap at 8"). frames/hist grew to 14 GB on a disk with room, because the
only retention governor was the free-disk floor. HIST_CAP_GB (TV_HIST_CAP_GB, default 8, 0 = off) now arms the
SAME evidence-aware shed under a healthy disk. Driven through the SHIPPED archive_read_frame over temp shelves:
  1. over the cap, the oldest loose footage goes and newer + young footage stays;
  2. a cap of 0 sheds nothing on a healthy disk;
  3. over the cap while recording (young loose frames present), sealed reels still go oldest first, and the two
     newest reels (the active one) are never taken.
"""
import os
import sys
import time
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import tv_diablo as T  # noqa: E402
from test_an_evidence_picture_is_never_reaped import _Shelf, _Usage, _jpg, GB, NOW_MS  # noqa: E402

MB = 1 << 20


def _blob(path, size=MB, age_s=None):
    with open(path, "wb") as fh:
        fh.write(b"\xff\xd8\xff" + b"\0" * (size - 5) + b"\xff\xd9")
    if age_s is not None:
        t = time.time() - age_s
        os.utime(path, (t, t))


def _tree_bytes(d):
    return sum(os.path.getsize(os.path.join(r, f)) for r, _x, fs in os.walk(d) for f in fs)


class TheCapShedsOldestFirst(_Shelf):

    def setUp(self):
        super().setUp()
        self.ledgers(accum={"owned": []}, chron={"uniques": {}, "sets": {}})
        self.src = os.path.join(self.root, "live.jpg")
        _jpg(self.src, 40, 30)

    def press(self, cap_gb, n=1):
        with mock.patch.object(T, "HIST_CAP_GB", cap_gb), \
                mock.patch("shutil.disk_usage", return_value=_Usage(50.0 * GB)):
            T._ORPHAN_DUE = 0.0
            return T.archive_read_frame(self.src, n, NOW_MS + n)

    def test_the_oldest_loose_footage_goes_and_the_newest_stays(self):
        old = ["f_%d.jpg" % (NOW_MS - k * 1000) for k in (30000, 20000, 10000)]
        for age, name in zip((3 * 3600, 2 * 3600, 3600), old):
            _blob(os.path.join(self.hist, name), age_s=age)
        young = "f_%d.jpg" % (NOW_MS - 60000)
        _blob(os.path.join(self.hist, young), age_s=60)
        cap = (_tree_bytes(self.hist) - MB // 2) / float(1 << 30)
        self.press(cap)
        left = set(os.listdir(self.hist))
        self.assertNotIn(old[0], left, "over the cap on a healthy disk, the oldest footage was not shed")
        self.assertIn(old[1], left, "the cap took more than it needed")
        self.assertIn(old[2], left)
        self.assertIn(young, left, "the youth shield was broken by the cap")

    def test_a_cap_of_zero_sheds_nothing(self):
        name = "f_%d.jpg" % (NOW_MS - 10 ** 7)
        _blob(os.path.join(self.hist, name), age_s=3 * 3600)
        self.press(0.0)
        self.assertIn(name, os.listdir(self.hist))
        with mock.patch.object(T, "HIST_CAP_GB", 0.0):
            self.assertEqual(0, T._hist_over_cap(self.hist), "a cap of 0 still measured an excess")

    def test_reels_go_oldest_first_but_never_the_active_one(self):
        R = ["reel_s_150000000000%d_%d" % (i, i) for i in range(1, 5)]
        for i, r in enumerate(R):
            os.makedirs(os.path.join(self.hist, r))
            for k in range(2):
                _blob(os.path.join(self.hist, r, "f_15%011d.jpg" % (i * 10 + k)), age_s=4 * 3600)
        young = "f_%d.jpg" % (NOW_MS - 30000)        # the session being recorded right now
        _blob(os.path.join(self.hist, young), age_s=30)
        for n in range(1, 6):
            self.press(1e-6, n)
        left = set(os.listdir(self.hist))
        self.assertNotIn(R[0], left, "over the cap while recording, the oldest sealed reel was never reached")
        self.assertNotIn(R[1], left)
        self.assertIn(R[2], left, "one of the two newest reels was taken by the cap")
        self.assertIn(R[3], left, "the active (newest) reel was taken by the cap")
        self.assertEqual(2, len(os.listdir(os.path.join(self.hist, R[3]))))
        self.assertIn(young, left, "the frame being recorded was taken by the cap")


RED_PROOF = [
    {"why": "The cap never arms the shed (only the free-disk floor does, as before).",
     "file": "tv/tv_diablo.py",
     "find": "            if free_gb < MIN_FREE_GB or _over:\n",
     "replace": "            if free_gb < MIN_FREE_GB:\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main()
