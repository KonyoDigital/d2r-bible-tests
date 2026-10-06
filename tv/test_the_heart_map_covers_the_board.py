# -*- coding: utf-8 -*-
"""#41 rank 25 (REG-1538, 2026-09-29) — THE HEART MAP COVERS THE BOARD (bible.html), NOT ONLY THE CONSOLE PAGE.

The heart audit (verified list, rank 25): "heart_map reads only control_ui.html, so bible.html's builder and mule
surfaces can never be counted as watched or unwatched." Measured before the fix: 513 ids on the board, 81 of them
cb-* / chars-* / mp-* / vault-*, and HEART.md said nothing about any of them — a silence that read exactly like a
map that had checked them.

WHAT THIS LAW DRIVES, over the real tree and over stand-ins for the unreadable cases:
  · measure_pages() measures BOTH pages by the console's own rule: the board's ids are a real list (hundreds, holding
    the builder's #cb-modal and the Characters tab's #chars-list), and its watched list is a measurement (a list,
    never None) when every watcher reads.
  · render() carries a board table whose three figures are the board's measurement, under its own heading, after
    the console's unchanged table.
  · UNKNOWN IS A REFUSAL AT EVERY DOOR: with bible.html unreadable, render() raises naming bible.html (and only it),
    and main(["--check"]) returns 1 saying so — never a board table of zeros.
  · THE BOARD'S OWN RATCHET: --check refuses when the floor has no "board" entry (never measured is UNKNOWN, not
    clean), refuses when the board's watched count FELL below its floor naming the surface that is no longer
    watched, and passes when both pages hold their floors. --bless writes the board's floor beside the console's.
  · THE COMMITTED MAP IS CURRENT: on this tree main(["--check"]) is 0 — HEART.md and heart_floor.json match the
    code, as the pre-push demands.
RED_PROOF below.
"""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from console_safe import enable; enable()

import heart_map as HM


class _Quiet(object):
    """swallow main()'s prints and keep them for the assertions"""
    def __init__(self):
        self.lines = []

    def write(self, s):
        self.lines.append(s)

    def flush(self):
        pass


def _main(argv):
    q, real = _Quiet(), sys.stdout
    sys.stdout = q
    try:
        rc = HM.main(argv)
    finally:
        sys.stdout = real
    return rc, "".join(q.lines)


class TheHeartMapCoversTheBoard(unittest.TestCase):

    def setUp(self):
        self.real_read, self.real_out, self.real_floor = HM._read, HM.OUT, HM.FLOOR
        self.tmp = tempfile.mkdtemp(prefix="heart-map-board-")

    def tearDown(self):
        HM._read, HM.OUT, HM.FLOOR = self.real_read, self.real_out, self.real_floor
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _scratch(self, floor):
        """route the map's writes into the temp dir: a real check over a floor of this law's choosing"""
        HM.OUT = os.path.join(self.tmp, "HEART.md")
        HM.FLOOR = os.path.join(self.tmp, "heart_floor.json")
        io.open(HM.OUT, "w", encoding="utf-8").write(HM.render())
        if floor is not None:
            io.open(HM.FLOOR, "w", encoding="utf-8").write(json.dumps(floor))

    def test_both_pages_are_measured_and_the_board_holds_the_builder_and_the_characters_tab(self):
        pages, missing = HM.measure_pages()
        self.assertEqual([], missing)
        self.assertEqual({"control_ui.html", "bible.html"}, set(pages))
        board = pages["bible.html"]
        self.assertIsNotNone(board["ids"], "the board page could not be read")
        self.assertGreater(len(board["ids"]), 400, "the board's ids are not the board's: %d" % len(board["ids"]))
        for sid in ("cb-modal", "chars-list", "vault-detail"):
            self.assertIn(sid, board["ids"], "the board's %s is not among its surfaces" % sid)
        self.assertIsInstance(board["seen"], list, "the board's watched list is not a measurement")
        console = pages["control_ui.html"]
        ids, seen, _m = HM.measure()
        self.assertEqual((ids, seen), (console["ids"], console["seen"]), "the console's figures moved")

    def test_the_map_carries_a_board_table_with_the_boards_own_figures(self):
        pages, _m = HM.measure_pages()
        b = pages["bible.html"]
        text = HM.render()
        i = text.index("## The board")
        self.assertIn("| surfaces the board paints | **%d** |" % len(b["ids"]), text[i:])
        self.assertIn("| of those, watched | **%d** |" % len(b["seen"]), text[i:])
        self.assertIn("### Watched on the board", text[i:])
        self.assertLess(text.index("| surfaces the console paints |"), i, "the board's table precedes the console's")
        # REG-1893 - an unreadable watcher leaves `seen` empty and this loop would pass having listed nothing.
        self.assertTrue(b["seen"], "no board surface was measured as watched, so the list check below "
                                   "would judge nothing")
        for name in b["seen"]:
            self.assertIn("- `%s`" % name, text[i:])

    def test_an_unreadable_board_is_a_refusal_naming_the_board(self):
        HM._read = lambda name: None if name == "bible.html" else self.real_read(name)
        with self.assertRaises(RuntimeError) as cm:
            HM.render()
        self.assertIn("bible.html could not be read", str(cm.exception))
        self.assertNotIn("control_ui.html could not be read", str(cm.exception), "a healthy page was named first")
        rc, out = _main(["--check"])
        self.assertEqual(1, rc)
        self.assertIn("bible.html could not be read", out)

    def test_the_boards_ratchet_refuses_an_unblessed_floor_and_a_fall_and_passes_a_held_floor(self):
        pages, _m = HM.measure_pages()
        c, b = pages["control_ui.html"], pages["bible.html"]
        base = {"watched": len(c["seen"]), "surfaces": len(c["ids"]), "names": c["seen"]}
        # never measured: UNKNOWN, refused
        self._scratch(dict(base))
        rc, out = _main(["--check"])
        self.assertEqual(1, rc, out)
        self.assertIn("no board floor", out)
        # a fall: a surface the board used to watch is no longer watched, named
        self._scratch(dict(base, board={"watched": len(b["seen"]) + 1, "surfaces": len(b["ids"]),
                                        "names": b["seen"] + ["cb-modal-ghost"]}))
        rc, out = _main(["--check"])
        self.assertEqual(1, rc, out)
        self.assertIn("on the board FELL", out)
        self.assertIn("cb-modal-ghost", out)
        # held: passes, and says both pages
        self._scratch(dict(base, board={"watched": len(b["seen"]), "surfaces": len(b["ids"]), "names": b["seen"]}))
        rc, out = _main(["--check"])
        self.assertEqual(0, rc, out)
        self.assertIn("board: %d of %d watched" % (len(b["seen"]), len(b["ids"])), out)

    def test_bless_writes_the_boards_floor_beside_the_consoles(self):
        self._scratch(None)
        rc, _out = _main(["--bless"])
        self.assertEqual(0, rc)
        fl = json.load(io.open(HM.FLOOR, encoding="utf-8"))
        pages, _m = HM.measure_pages()
        self.assertEqual(len(pages["control_ui.html"]["seen"]), fl["watched"])
        self.assertEqual({"watched": len(pages["bible.html"]["seen"]), "surfaces": len(pages["bible.html"]["ids"]),
                          "names": pages["bible.html"]["seen"]}, fl["board"])
        self.assertIn("## The board", io.open(HM.OUT, encoding="utf-8").read())

    def test_the_committed_map_and_floor_are_current(self):
        rc, out = _main(["--check"])
        self.assertEqual(0, rc, "HEART.md / heart_floor.json are stale on this tree: %s" % out)


RED_PROOF = [
    {
        "why": "#41 rank 25 - the board leaves the page list: the map goes back to the console alone",
        "file": "heart_map.py",
        "find": "PAGES = ((\"control_ui.html\", \"the console\"), (\"bible.html\", \"the board\"))\n",
        "replace": "PAGES = ((\"control_ui.html\", \"the console\"),)\n",
        "matches": 1,
    },
    {
        "why": "#41 rank 25 - the board is looked for in tv/, where it is not: unreadable, and the map must refuse",
        "file": "heart_map.py",
        "find": "        with io.open(os.path.join(REPO if name == BOARD else HERE, name), encoding=\"utf-8\") as fh:\n",
        "replace": "        with io.open(os.path.join(HERE, name), encoding=\"utf-8\") as fh:\n",
        "matches": 1,
    },
    {
        "why": "#41 rank 25 - the board's ratchet is skipped: a floor with no board entry passes as clean",
        "file": "heart_map.py",
        "find": "        if not isinstance(bfl, dict):\n            print(\"heart_floor.json carries no board floor",
        "replace": "        if False:\n            print(\"heart_floor.json carries no board floor",
        "matches": 1,
    },
    {
        "why": "#41 rank 25 - a fall on the board no longer refuses",
        "file": "heart_map.py",
        "find": "        if len(bseen) < bwas:\n",
        "replace": "        if False:\n",
        "matches": 1,
    },
]


if __name__ == "__main__":
    unittest.main(verbosity=2)
