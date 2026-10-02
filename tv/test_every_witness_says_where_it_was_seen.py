# -*- coding: utf-8 -*-
"""#234/#146 (v3552) - EVERY WITNESSED ITEM SAYS WHERE IT WAS SEEN, FROM NOW ON.

His words, 2026-10-01: "i remember we said that the items being witnessed also need coordinates based on where they were
witnessed", and on the cost of asking: "thats even better" to asking from now on without re-reading his old footage.
MEASURED that night: 158 vault looks and every deep read on his Mac carried NO point and NO slot word - only a lane
(stash | inventory | equipped). The parser and the ledger's corroborator pair (the reader's slot WORD against the point's
GEOMETRY) were built for them; the reader was simply never asked (REG-1522).

What this law drives:
  * the question - READ_PROMPT asks every named item's point (the ITEM, never its tooltip) and an equipped item's doll
    slot, in exactly the doll's own words (slot_identity.DOLL_SLOTS)
  * forward only - p1839's seals still stand and its per-frame read counts still count under p3552, so nothing he filmed
    is bought again; a reader that asked a DIFFERENT question still reopens
  * the space - a read that pointed carries the [w, h] of the picture it pointed in (`xySpace`), and the deep-read row
    keeps it
  * the placing - equipped_ledger scales a point from the reader's picture to the frame it files against, so a point
    measured on a downscaled copy still lands in the right doll slot (his Mac's frames: 1440x904)
RED_PROOF below.
"""
import io
import os
import shutil
import struct
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

_WORLD = tempfile.mkdtemp(prefix="witness_where_")
os.environ["TV_HIST"] = _WORLD
os.environ["TV_SESSIONS"] = os.path.join(_WORLD, "sessions.jsonl")

import tv_diablo as tv  # noqa: E402
import control_app as ca  # noqa: E402
import equipped_ledger as EL  # noqa: E402
import slot_identity as SI  # noqa: E402


def _jpeg(path, w, h):
    """A JPEG header with a real SOF0 marker - all jpeg_size reads."""
    sof = b"\xff\xc0" + struct.pack(">H", 17) + b"\x08" + struct.pack(">HH", h, w) + b"\x03" + b"\x01\x22\x00" * 3
    with open(path, "wb") as fh:
        fh.write(b"\xff\xd8" + sof + b"\xff\xd9")


class TheReaderIsAskedWhere(unittest.TestCase):

    def setUp(self):
        self.p = tv.READ_PROMPT.format(path="IMG")

    def test_the_answer_shape_has_a_point_and_a_slot_for_every_name(self):
        self.assertIn('"names_xy":{}', self.p)
        self.assertIn('"names_slot":{}', self.p)
        self.assertIn("NEVER the tooltip box", self.p, "a point on the tooltip would file the item where the tooltip floats")

    def test_the_slot_words_are_the_dolls_own(self):
        i = self.p.index("names_slot = ONLY")
        line = self.p[i:self.p.index("\n", i)]
        asked = [w.strip() for w in line.split("one of", 1)[1].split("(")[0].split("|")]
        self.assertEqual(sorted(asked), sorted(SI.DOLL_SLOTS), "the reader is asked in other words than the doll's")

    def test_the_parser_keeps_what_the_reader_points_at(self):
        r = tv._parse_read('{"scene":"inventory","names":["Shako"],"names_loc":{"Shako":"equipped"},'
                           '"names_xy":{"Shako":[1085,329]},"names_slot":{"Shako":"torso"}}')
        self.assertEqual(r.get("names_xy"), {"Shako": [1085.0, 329.0]})
        self.assertEqual(r.get("names_slot"), {"Shako": "torso"})


class NothingHeFilmedIsBoughtAgain(unittest.TestCase):

    def test_a_p1839_seal_still_stands(self):
        self.assertEqual(tv.PROMPT_ANSWERS_SAME_AS, ("p1839",))
        self.assertTrue(ca._chron_seal_stands({"pages": 0, "promptVer": "p1839"}),
                        "an old 'nothing here' seal reopened - every old reel would be read and paid for again")
        self.assertTrue(ca._chron_seal_stands({"pages": 0, "promptVer": tv.PROMPT_VER}))

    def test_a_reader_that_asked_a_different_question_still_reopens(self):
        self.assertFalse(ca._chron_seal_stands({"pages": 0, "promptVer": "p1509"}))
        self.assertFalse(ca._chron_seal_stands({"pages": 0, "promptVer": "p1839"}, "p-other"),
                         "the same-as list leaked onto a reader that is not the current one")

    def test_reads_made_under_p1839_still_count_against_the_cap(self):
        reads = {"p1839": {"reel_a|f_1": ca._CHRON_READ_CAP}}
        self.assertIsNotNone(ca._chron_read_capped(reads, tv.PROMPT_VER, "reel_a", "f_1"),
                             "a frame read to its cap under p1839 was offered for reading again")
        self.assertIsNone(ca._chron_read_capped({"p1509": {"reel_a|f_1": 9}}, tv.PROMPT_VER, "reel_a", "f_1"))


class APointCarriesItsSpace(unittest.TestCase):

    def setUp(self):
        self.td = tempfile.mkdtemp(prefix="witness_space_")
        self.addCleanup(shutil.rmtree, self.td, True)

    def test_a_read_that_pointed_carries_the_size_of_the_picture(self):
        pic = os.path.join(self.td, "read.jpg")
        _jpeg(pic, 720, 452)
        rd = tv._with_xy_space({"names": ["Shako"], "names_xy": {"Shako": [542.9, 164.3]}}, pic)
        self.assertEqual(rd.get("xySpace"), [720, 452])
        self.assertNotIn("xySpace", tv._with_xy_space({"names": ["Shako"], "names_xy": {}}, pic))
        rd = tv._with_xy_space({"names_xy": {"Shako": [1, 2]}}, os.path.join(self.td, "absent.jpg"))
        self.assertIsNone(rd.get("xySpace"), "a size nobody could read must be UNKNOWN, not the frame's")

    def test_the_deep_read_row_keeps_the_space(self):
        with io.open(os.path.join(HERE, "tv_diablo.py"), encoding="utf-8") as fh:
            src = fh.read()
        self.assertEqual(src.count('        "xySpace": rd.get("xySpace"),'), 1)


class ThePointLandsInTheRightSlot(unittest.TestCase):
    """his Mac's frames are 1440x904; a reader shown a half-size copy points at 720x452"""

    def setUp(self):
        self.hist = tempfile.mkdtemp(prefix="witness_hist_")
        self.addCleanup(shutil.rmtree, self.hist, True)
        os.makedirs(os.path.join(self.hist, "reel_s_1"))
        _jpeg(os.path.join(self.hist, "reel_s_1", "f_1.jpg"), 1440, 904)
        x, y, w, h = SI.EQUIP_SLOTS["torso"]
        self.centre_half = [(x + w / 2) * 720, (y + h / 2) * 452]

    def _row(self, space, word=None):
        row = {"sessionId": "s_1", "frameId": "f_1", "names_loc": {"Shako": "equipped"},
               "names_xy": {"Shako": list(self.centre_half)}, "names_slot": ({"Shako": word} if word else {})}
        if space is not None:
            row["xySpace"] = space
        return row

    def test_a_point_from_a_half_size_picture_lands_in_its_slot(self):
        got = EL.worn_from_row(self._row([720, 452]), self.hist)
        self.assertEqual(len(got), 1, got)
        self.assertEqual(got[0]["slot"], "torso", got[0])
        self.assertEqual(got[0]["slotBy"], "geometry")

    def test_the_word_and_the_scaled_point_agree(self):
        got = EL.worn_from_row(self._row([720, 452], word="torso"), self.hist)
        self.assertEqual(got[0]["slotBy"], "reader+geometry", got[0])

    def test_a_point_whose_picture_size_is_unknown_is_never_placed(self):
        """REG-1707 (the v3552 eye) - xySpace null: even a point that WOULD land in a doll box stays unplaced"""
        x, y, w, h = SI.EQUIP_SLOTS["torso"]
        row = {"sessionId": "s_1", "frameId": "f_1", "names_loc": {"Shako": "equipped"},
               "names_xy": {"Shako": [(x + w / 2) * 1440, (y + h / 2) * 904]}, "names_slot": {}, "xySpace": None}
        got = EL.worn_from_row(row, self.hist)
        self.assertIsNone(got[0]["slot"], got[0])
        self.assertIn("unknown", got[0]["why"])
        self.assertIsNone(got[0]["xy"])

    def test_without_its_space_the_same_point_is_not_placed(self):
        """premise: unscaled, the half-size point lies off the doll - so the case above can only pass by scaling"""
        got = EL.worn_from_row(self._row(None), self.hist)
        self.assertIsNone(got[0]["slot"], got[0])


RED_PROOF = [
    {
        "why": "REG-1707 - a point whose picture size is unknown is filed on the frame's grid again",
        "file": "equipped_ledger.py",
        "find": "            if _sp_unknown:\n                geo_why = \"the size of the picture the point was measured in is unknown, so it cannot be placed\"\n            elif size is None:\n",
        "replace": "            if size is None:\n",
        "matches": 1,
    },
    {
        "why": "v3552 - the reader stops being asked where each item is",
        "file": "tv_diablo.py",
        "find": "\\\"names_slot\\\":{{}},\\\"names_xy\\\":{{}},",
        "replace": "",
        "matches": 1,
    },
    {
        "why": "v3552 - an old 'nothing here' seal reopens: every old reel is read and paid for again",
        "file": "control_app.py",
        "find": "    return have in _prompt_vers_same_as(want)\n",
        "replace": "    return False\n",
        "matches": 1,
    },
    {
        "why": "v3552 - frames read to their cap under p1839 are offered for reading again",
        "file": "control_app.py",
        "find": "               for v in (str(prompt_ver),) + _prompt_vers_same_as(prompt_ver))\n",
        "replace": "               for v in (str(prompt_ver),))\n",
        "matches": 1,
    },
    {
        "why": "v3552 - a read that pointed no longer says the size of the picture it pointed in",
        "file": "tv_diablo.py",
        "find": "    rd[\"xySpace\"] = [int(_sz[0]), int(_sz[1])] if _sz else None\n",
        "replace": "    rd[\"xySpace\"] = None\n",
        "matches": 1,
    },
    {
        "why": "v3552 - the ledger stops scaling a point to its frame, so a downscaled read files in the wrong slot",
        "file": "equipped_ledger.py",
        "find": "                    pt = (pt[0] * float(size[0]) / float(_sp[0]), pt[1] * float(size[1]) / float(_sp[1]))\n",
        "replace": "                    pt = pt\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
