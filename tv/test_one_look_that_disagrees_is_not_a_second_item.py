# -*- coding: utf-8 -*-
"""#207 (REG-2037) - ONE LOOK THAT DISAGREES IS NOT A SECOND ITEM, AND A RUNEWORD HAS NO READER QUALITY.

From the 2026-10-07 simulation pass on his real reels (F6). His seen bank holds Grief: one session, three reads 1.4-3 s
apart, 5 sockets each - eth True once, False twice. The tooltip at native 1440x936 has no Ethereal line. _variants_of
counted (5, True) and (5, False) as two physical items, so the row carried an ethereal Grief nobody owns. And Heart of
the Oak / Enlightenment were read 'unique', 'blue' and 'gold' - a runeword's name colour is not a quality the reader can
give.

  * same session, same sockets, no cell telling them apart, eth reads disagree -> ONE variant, eth UNKNOWN (None), the
    reads beside it as ethReads - never True from a minority, never False by fiat;
  * different cells (or different sessions) stay different items - an eth Phase Blade Grief and a plain one are both
    real;
  * a runeword's variant carries quality None; any other item keeps what the reader saw.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import vault_retro as vr  # noqa: E402


def _look(frame, eth, session="s_1789419985817_32179", cell=None, quality="unique", sockets=5):
    e = {"session": session, "frame": frame, "lane": "stash", "conf": 0.9, "ts": 1,
         "sockets": sockets, "eth": eth, "quality": quality}
    if cell is not None:
        e["cell"] = cell
    return e


class OneLookThatDisagreesIsNotASecondItem(unittest.TestCase):

    def test_his_grief_is_one_item_whose_eth_is_unknown(self):
        v = vr._variants_of([_look("f_1789420016803", True), _look("f_1789420019790", False),
                             _look("f_1789420021159", False)], "Grief")
        self.assertEqual(len(v), 1, "one disagreeing read became a second Grief: %r" % v)
        self.assertIsNone(v[0]["eth"], "a minority read decided the eth: %r" % v)
        self.assertEqual(v[0]["witnesses"], 3)
        self.assertEqual(v[0].get("ethReads"), {"eth": 1, "notEth": 2}, v)

    def test_agreeing_reads_keep_their_eth(self):
        v = vr._variants_of([_look("a", True), _look("b", True)], "Grief")
        self.assertEqual([(x["eth"], x["witnesses"]) for x in v], [(True, 2)], v)
        self.assertNotIn("ethReads", v[0])

    def test_two_cells_are_two_items(self):
        v = vr._variants_of([_look("a", True, cell="r1c1"), _look("b", False, cell="r1c3")], "Grief")
        self.assertEqual(sorted(x["eth"] for x in v), [False, True], "two cells were merged into one item: %r" % v)

    def test_two_sessions_are_two_items(self):
        v = vr._variants_of([_look("a", True, session="s_1"), _look("b", False, session="s_2")], "Grief")
        self.assertEqual(len(v), 2, v)

    def test_a_runeword_carries_no_reader_quality_and_an_item_keeps_its_own(self):
        rw = vr._variants_of([_look("a", False, quality="unique"), _look("b", False, quality="blue"),
                              _look("c", False, quality="gold")], "Heart of the Oak")
        self.assertEqual([(x["quality"], x["witnesses"]) for x in rw], [(None, 3)], rw)
        it = vr._variants_of([_look("a", False, quality="white", sockets=4)], "Gorgon Crossbow")
        self.assertEqual(it[0]["quality"], "white", it)
        self.assertTrue(vr._is_runeword("Heart of the Oak"))
        self.assertFalse(vr._is_runeword("Gorgon Crossbow"))


RED_PROOF = [
    {"why": "REG-2037 - one disagreeing eth read becomes a second item again",
     "file": "vault_retro.py",
     "find": "        if True in eths and False in eths:\n",
     "replace": "        if False:\n",
     "matches": 1},
    {"why": "REG-2037 - a runeword carries the reader's name colour as its quality again",
     "file": "vault_retro.py",
     "find": "    rw = _is_runeword(name)\n",
     "replace": "    rw = False\n",
     "matches": 1},
]


if __name__ == "__main__":
    unittest.main(verbosity=1)
