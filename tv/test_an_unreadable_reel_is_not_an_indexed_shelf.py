# -*- coding: utf-8 -*-
"""REG-1796 — AN UNREADABLE REEL IS NOT AN INDEXED SHELF.

REG-1732 made a shelf that will not list come back as None, and the doctor says
that is unknown. One reel directory under a shelf that did list still went
through _reel_jpg_count, and that helper returns 0 when the directory will not
list. Zero is also a reel that holds no frames, so the shelf omitted it and the
row said every reel had an index.

A reel whose index is present is still indexed. A reel that listed and held no
frames is still not this warn. A shelf that is not there yet is still empty.
One reel that will not list makes the whole shelf unknown, including when
another reel on it is already missing its index. The doctor still refuses that
None. Nothing here reads his live shelf.

RED_PROOF below. [[unknown-stays-unknown]]
"""
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

_DOCTOR_NONE = "    if _noidx is None:\n"
_DOCTOR_SAY = "frames/hist exists but could not be read"


class AnUnreadableReelIsNotAnIndexedShelf(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="idxshelf_")
        self.addCleanup(shutil.rmtree, self.d, True)

    def _reel(self, name, frames=0, index=False):
        rd = os.path.join(self.d, name)
        os.makedirs(rd)
        for i in range(frames):
            with open(os.path.join(rd, "f_%04d.jpg" % (i + 1)), "wb"):
                pass
        if index:
            with open(os.path.join(rd, "index.json"), "w", encoding="utf-8") as fh:
                fh.write("{}")
        return rd

    def test_a_shelf_that_is_not_there_is_empty(self):
        self.assertEqual(ca._reels_missing_index(os.path.join(self.d, "never_filmed")), [])

    def test_a_readable_reel_with_frames_and_no_index_is_listed(self):
        self._reel("reel_s_1_ok", frames=2)
        got = ca._reels_missing_index(self.d)
        self.assertEqual([n for n, _c in (got or [])], ["reel_s_1_ok"], got)

    def test_a_readable_reel_with_no_frames_is_not_this_warn(self):
        self._reel("reel_s_3_empty", frames=0)
        self.assertEqual(ca._reels_missing_index(self.d), [])

    def test_a_reel_whose_index_is_present_stays_indexed_when_its_frames_will_not_list(self):
        self._reel("reel_s_2_idx", frames=0, index=True)
        real = os.listdir

        def _refuse(path):
            if os.path.basename(path) == "reel_s_2_idx":
                raise PermissionError(13, "Permission denied", path)
            return real(path)

        with mock.patch.object(ca.os, "listdir", _refuse):
            self.assertEqual(ca._reels_missing_index(self.d), [])

    def test_one_unreadable_reel_makes_the_shelf_unknown(self):
        # The readable one is missing its index. Omitting the unreadable one would
        # still publish a list, and a list is a measurement the doctor can pass.
        self._reel("reel_s_1_ok", frames=1)
        self._reel("reel_s_9_bad", frames=1)
        real = os.listdir

        def _refuse(path):
            if os.path.basename(path) == "reel_s_9_bad":
                raise PermissionError(13, "Permission denied", path)
            return real(path)

        with mock.patch.object(ca.os, "listdir", _refuse):
            got = ca._reels_missing_index(self.d)
        self.assertIsNone(got, "an unreadable reel was omitted and the shelf still looked measured: %r" % (got,))

    def test_the_doctor_still_refuses_that_unknown(self):
        path = os.path.join(HERE, "control_app.py")
        with open(path, encoding="utf-8") as f:
            src = f.read()
        self.assertEqual(src.count(_DOCTOR_NONE), 1)
        i = src.find(_DOCTOR_NONE)
        end = src.find("\n    else:\n", i)        # REG-1842: the unknown arm's own end, not a guessed width
        self.assertGreater(end, i, "the doctor's unknown arm moved")
        self.assertIn(_DOCTOR_SAY, src[i:end])


RED_PROOF = [
    {
        "why": "REG-1796 - a reel directory that will not list is skipped, so the shelf "
               "returns the other reels and the doctor can say they are indexed",
        "file": "control_app.py",
        "find": "        try:\n            frame_names = os.listdir(rd)\n        except Exception:\n            return None\n",
        "replace": "        try:\n            frame_names = os.listdir(rd)\n        except Exception:\n            continue\n",
        "matches": 1,
    },
    {
        "why": "REG-1796 - the doctor drops the unknown door, and None falls through to "
               "not _noidx, which is a pass",
        "file": "control_app.py",
        "find": "    if _noidx is None:\n",
        "replace": "    if False:\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
