# -*- coding: utf-8 -*-
"""REG-1811 — AN UNREAD SHELF IS NOT AN EMPTY EXTRACT.

The reel-extract row treats a shelf that will not list as "no reels on
disk — nothing to extract", and the row stays ok. reel_dirs returns []
when the listing raises, and [] is also a shelf that holds no reels.

A shelf that lists and holds nothing still says nothing to extract. A
reel that is there still owes a read. A missing shelf is still no
frames/hist. An unread shelf says the list was not read, and the row
does not stay ok.

Nothing here reads his shelf or his sweep memory. RED_PROOF below.
[[unknown-stays-unknown]]
"""
import inspect
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

import console_doctor as cd  # noqa: E402
import control_app as ca  # noqa: E402


_EMPTY = "no reels on disk — nothing to extract"
_UNREAD = "an unread shelf is not an empty one"
_MISSING_SHELF = "no frames/hist on this machine"


def _frame(reel_dir):
    os.makedirs(reel_dir)
    with open(os.path.join(reel_dir, "f_1780000000000.jpg"), "wb") as fh:
        fh.write(b"\xff\xd8\xff\xe0" + b"0" * 32)


class AnUnreadShelfIsNotAnEmptyExtract(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="unread_shelf_1811_")
        self.addCleanup(shutil.rmtree, self.root, True)
        self.hist = os.path.join(self.root, "hist")
        os.makedirs(self.hist)
        self.swept = os.path.join(self.root, "chronicle_swept.json")
        self._saved = {k: os.environ.get(k) for k in ("TV_HIST", "TV_CHRON_SWEPT")}
        os.environ["TV_HIST"] = self.hist
        os.environ["TV_CHRON_SWEPT"] = self.swept
        self.addCleanup(self._restore_env)

    def _restore_env(self):
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def _ask(self):
        with mock.patch.object(ca, "_chron_reels_seen", return_value=set()):
            return cd._check_the_reel_extract_is_moving()

    def test_an_empty_shelf_is_still_nothing_to_extract(self):
        state, why = self._ask()
        self.assertEqual(state, cd.OK, why)
        self.assertIn(_EMPTY, why)
        self.assertNotIn(_UNREAD, why)

    def test_a_shelf_of_only_notes_is_still_nothing_to_extract(self):
        with open(os.path.join(self.hist, "notes.txt"), "w", encoding="utf-8") as fh:
            fh.write("not a reel")
        state, why = self._ask()
        self.assertEqual(state, cd.OK, why)
        self.assertIn(_EMPTY, why)
        self.assertNotIn(_UNREAD, why)

    def test_a_missing_shelf_is_still_no_frames_hist(self):
        os.environ["TV_HIST"] = os.path.join(self.root, "no-such-hist")
        state, why = self._ask()
        self.assertEqual(state, cd.UNKNOWN, why)
        self.assertIn(_MISSING_SHELF, why)
        self.assertNotIn(_EMPTY, why)
        self.assertNotIn(_UNREAD, why)

    def test_a_reel_on_a_readable_shelf_still_owes_a_read(self):
        _frame(os.path.join(self.hist, "reel_unread_shelf_1811"))
        state, why = self._ask()
        self.assertEqual(state, cd.MISSING, why)
        self.assertIn("1 reel(s) owe a read", why)
        self.assertIn("no read has ever been banked", why)
        self.assertNotIn(_EMPTY, why)
        self.assertNotIn(_UNREAD, why)

    def test_an_unread_shelf_is_not_nothing_to_extract(self):
        def refuse(_path):
            raise PermissionError("denied")

        with mock.patch("os.listdir", side_effect=refuse):
            state, why = self._ask()
        self.assertEqual(state, cd.UNKNOWN, why)
        self.assertIn(_UNREAD, why)
        self.assertIn("PermissionError", why)
        self.assertNotIn(_EMPTY, why)
        self.assertNotEqual(state, cd.OK)

    def test_the_extract_row_asks_the_shelf_before_it_says_empty(self):
        src = inspect.getsource(cd._check_the_reel_extract_is_moving)
        self.assertEqual(src.count("os.listdir(hist)"), 1)
        self.assertEqual(src.count("an unread shelf is not"), 1)
        self.assertEqual(src.count(_EMPTY), 1)


RED_PROOF = [
    {
        "why": "REG-1811 - an unread shelf is painted as nothing to extract",
        "file": "console_doctor.py",
        "find": "        try:\n"
                "            os.listdir(hist)\n"
                "        except OSError as e:\n"
                "            return UNKNOWN, (\"could not list reels (%s: %s) — an unread shelf is not \"\n"
                "                             \"an empty one\" % (type(e).__name__, str(e)[:60]))\n",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "REG-1811 - an empty shelf is painted as an unread one",
        "file": "console_doctor.py",
        "find": "        try:\n"
                "            os.listdir(hist)\n"
                "        except OSError as e:\n"
                "            return UNKNOWN, (\"could not list reels (%s: %s) — an unread shelf is not \"\n"
                "                             \"an empty one\" % (type(e).__name__, str(e)[:60]))\n",
        "replace": "        return UNKNOWN, (\"could not list reels (forced) — an unread shelf is not \"\n"
                   "                         \"an empty one\")\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
