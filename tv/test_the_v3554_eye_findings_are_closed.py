# -*- coding: utf-8 -*-
"""REG-1713 - THE v3554 EYE FINDINGS, CLOSED (the Grok CLI's look at 6c3f41e0 and the #231 code seat's at 6c3f41e0 and
4a7e7b5d, 2026-10-02). Each was reproduced from the code before it was fixed; each case below drives the real function.

  1  a picture over the 1568 px read spec is one the reader shrank by its own rule: its points' space is UNKNOWN and
     they stay unplaced (_vault_xy_map), never filed at full-frame scale in a real cell with why None
  2  the item-facts doctor row measures the CURRENT reader on its own witnesses; the same-question readers (vp3368)
     stand in only while it has read nothing, and the sentence names which population it measured
  3  a re-read of the same look fills its point and cell into the stored witness (fill-only) instead of being dropped
  4  a two-element picture size that is not two positive numbers is UNKNOWN - the raw point is never placed
     (both Grok seats found this one independently)
  5  the seal log's fallback asks the FILESYSTEM whether TV_HIST is inside the tree (os.path.samefile), so a
     differently-cased spelling of his own frames/hist on his case-insensitive Mac is his world, not a fixture's
RED_PROOF below.
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
sys.path.insert(0, HERE)
import fixture_tmp as _fx_tmp  # noqa: E402
_fx_tmp.contain()

try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import tv_diablo as tv  # noqa: E402
import vault_retro as vr  # noqa: E402
import equipped_ledger as EL  # noqa: E402
import slot_identity as SI  # noqa: E402
import console_doctor as cd  # noqa: E402
import printer as PR  # noqa: E402

try:
    from PIL import Image as _Img
except Exception:          # pragma: no cover - Pillow is installed in CI, on his Mac and on his ALT
    _Img = None


def _jpeg(path, w, h):
    _Img.new("RGB", (w, h), (20, 20, 20)).save(path, quality=80)
    return path


@unittest.skipIf(_Img is None, "Pillow is absent - no frame can be built, UNMEASURED")
class OneAPictureOverTheSpecHasNoKnownSpace(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="eye3554_")
        self.addCleanup(shutil.rmtree, self.d, True)

    def test_a_frame_sent_raw_over_the_spec_is_unplaced(self):
        big = _jpeg(os.path.join(self.d, "f_big.jpg"), 2560, 1600)
        self.assertIsNone(tv._vault_xy_map(big, big),
                          "a 2560 px picture the reader shrank by its own rule was given a known space")

    def test_a_picture_within_the_spec_keeps_its_space(self):
        big = _jpeg(os.path.join(self.d, "f_big.jpg"), 2560, 1600)
        sent = _jpeg(os.path.join(self.d, "read.jpg"), 1568, 980)
        m = tv._vault_xy_map(big, sent)
        self.assertEqual(m["space"], [1568, 980])
        self.assertEqual(m["extent"], [2560, 1600])


class TwoTheDoctorMeasuresTheCurrentReader(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="eye3554_doc_")
        self.addCleanup(shutil.rmtree, self.d, True)
        self.cur = str(tv.VAULT_PROMPT_VER)
        self.old = str((tv.VAULT_PROMPT_ANSWERS_SAME_AS or ("vp-old",))[0])

    def _store(self, rows):
        with io.open(os.path.join(self.d, "vault_seen.json"), "w", encoding="utf-8") as fh:
            json.dump({"rows": rows}, fh)
        with mock.patch.object(cd, "HERE", self.d):
            return cd._check_the_item_facts_are_reaching_the_row()

    def test_a_current_read_that_dropped_the_facts_is_missing_beside_an_old_one_that_had_them(self):
        st, why = self._store([
            {"name": "Shako", "lane": "stash", "witnesses": [{"promptVer": self.old, "sockets": 2}]},
            {"name": "Arachnid Mesh", "lane": "stash", "witnesses": [{"promptVer": self.cur}]}])
        self.assertEqual(st, cd.MISSING, why)
        self.assertIn("read by %s" % self.cur, why)

    def test_only_the_old_reader_says_so(self):
        st, why = self._store([{"name": "Shako", "lane": "stash", "witnesses": [{"promptVer": self.old, "sockets": 2}]}])
        self.assertEqual(st, cd.OK, why)
        self.assertIn("has read nothing yet", why)


class ThreeAReReadFillsItsCell(unittest.TestCase):

    def _row(self, w):
        return {"name": "Shako", "lane": "stash", "kind": "item", "count": 1, "conf": 0.9, "lastSeenTs": 1,
                "witnesses": [w]}

    def test_the_same_look_read_again_brings_its_cell(self):
        have = {}
        vr._absorb(have, self._row({"session": "s1", "frame": "f1", "lane": "stash"}))
        vr._absorb(have, self._row({"session": "s1", "frame": "f1", "lane": "stash", "point": [530.5, 702.0],
                                    "cell": "stash:c3r4", "cellWhy": None}))
        w = have[("Shako", "stash")]["witnesses"]
        self.assertEqual(len(w), 1)
        self.assertEqual(w[0].get("cell"), "stash:c3r4", w)
        self.assertEqual(w[0].get("point"), [530.5, 702.0])

    def test_a_filed_cell_is_never_moved(self):
        have = {}
        vr._absorb(have, self._row({"session": "s1", "frame": "f1", "lane": "stash", "cell": "stash:c3r4"}))
        vr._absorb(have, self._row({"session": "s1", "frame": "f1", "lane": "stash", "cell": "stash:c9r9"}))
        self.assertEqual(have[("Shako", "stash")]["witnesses"][0]["cell"], "stash:c3r4")


@unittest.skipIf(_Img is None, "Pillow is absent - no frame can be built, UNMEASURED")
class FourAJunkPictureSizeIsUnknown(unittest.TestCase):

    def setUp(self):
        self.hist = tempfile.mkdtemp(prefix="eye3554_hist_")
        self.addCleanup(shutil.rmtree, self.hist, True)
        os.makedirs(os.path.join(self.hist, "reel_s_1"))
        _jpeg(os.path.join(self.hist, "reel_s_1", "f_1.jpg"), 1440, 904)
        (bx, by, bw, bh) = SI.frame_box(SI.EQUIP_SLOTS["torso"], 1440, 904)
        self.inside = [bx + bw / 2.0, by + bh / 2.0]           # a raw point that WOULD land in the torso box

    def _row(self, space):
        return {"sessionId": "s_1", "frameId": "f_1", "names_loc": {"Shako": "equipped"},
                "names_xy": {"Shako": list(self.inside)}, "names_slot": {}, "xySpace": space}

    def test_a_two_element_junk_size_never_places_the_raw_point(self):
        for junk in ([0, 0], [None, None], ["w", "h"], [True, True], [-1440, 904]):
            got = EL.worn_from_row(self._row(junk), self.hist)
            self.assertIsNone(got[0]["slot"], (junk, got[0]))
            self.assertIn("unknown", got[0]["why"], junk)
            self.assertIsNone(got[0]["xy"], junk)

    def test_premise_a_real_size_places_it(self):
        got = EL.worn_from_row(self._row([1440, 904]), self.hist)
        self.assertEqual(got[0]["slot"], "torso", got[0])


class FiveTheSealLogAsksTheFilesystem(unittest.TestCase):

    def test_a_case_different_spelling_of_the_tree_is_inside_it(self):
        d = tempfile.mkdtemp(prefix="eye3554_case_")
        self.addCleanup(shutil.rmtree, d, True)
        tree = os.path.join(d, "treedir")
        os.makedirs(os.path.join(tree, "frames", "hist"))
        variant = os.path.join(d, "TREEDIR", "frames", "hist")
        if not os.path.exists(variant):
            self.skipTest("this volume is case-SENSITIVE - the two spellings are two directories here, UNMEASURED")
        self.assertTrue(PR._inside_tree(variant, tree),
                        "an uppercased spelling of the same directory was read as outside the tree")

    def test_a_directory_outside_is_outside(self):
        a, b = tempfile.mkdtemp(prefix="eye3554_in_"), tempfile.mkdtemp(prefix="eye3554_out_")
        self.addCleanup(shutil.rmtree, a, True)
        self.addCleanup(shutil.rmtree, b, True)
        self.assertFalse(PR._inside_tree(b, a))


RED_PROOF = [
    {
        "why": "REG-1713 (1) - a picture over the read spec keeps its full-frame size as the reader's space again",
        "file": "tv_diablo.py",
        "find": "    if max(int(_ss[0]), int(_ss[1])) > _VAULT_READ_SPEC_PX:\n        return None\n",
        "replace": "    if False:\n        return None\n",
        "matches": 1,
    },
    {
        "why": "REG-1713 (2) - the doctor pools the old reader with the current one again",
        "file": "console_doctor.py",
        "find": "    mine, said = _by((ver,)), ver\n",
        "replace": "    mine, said = _by(_vers), ver\n",
        "matches": 1,
    },
    {
        "why": "REG-1713 (3) - a re-read of the same look is dropped whole again, cell and all",
        "file": "vault_retro.py",
        "find": "        if isinstance(old, dict) and isinstance(w, dict) and not old.get(\"cell\") and w.get(\"cell\"):\n",
        "replace": "        if False:\n",
        "matches": 1,
    },
    {
        "why": "REG-1713 (4) - a two-element junk picture size counts as known again and the raw point is placed",
        "file": "equipped_ledger.py",
        "find": "                      and not any(isinstance(v, bool) for v in _sp) and float(_sp[0]) > 0 and float(_sp[1]) > 0)\n",
        "replace": "                      )\n",
        "matches": 1,
    },
    {
        "why": "REG-1713 (5) - the seal log decides 'inside the tree' by string again; on his Mac a case spelling escapes",
        "file": "printer.py",
        "find": "            if os.path.exists(cur) and os.path.exists(b) and os.path.samefile(cur, b):\n                return True\n",
        "replace": "            if False:\n                return True\n",
        "matches": 1, "needs": "macos",
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
