# -*- coding: utf-8 -*-
"""THE OCCUPIED CELLS ARE EVIDENCE; THE CLUSTERS THEY FORM ARE NOT ITEMS.

His ask, 2026-09-13: *"all on ledger for the slot identity and for the tallied and for the witness
count and footprint and everything need to be ledgered meaning information based item wise"*.

⚠⚠ EVERY PIECE ALREADY EXISTED AND ONE LINE THREW THE USEFUL HALF AWAY.
`vault_corpus.inventory_occupancy` returns `{ok, occupied, free, cells, grid}` — `grid` being a
row-major 2D array of taken/None, read from PIXELS on a bimodal signal (an empty cell is uniformly
near-black, mean 4.3 std 0.6-1.0; an occupied one is 31-169 std 20-78, and three independent
threshold pairs return the same answer). The sweep kept only the two COUNTS, so
`slot_identity.item_groups` was never handed anything and the vault row could say "Bone Break,
stash" and never WHERE in the grid it sat. [[the-unjoined-end]]

⚠⚠ AND THE CLUSTERS ARE NOT ITEMS. `item_groups` joins ADJACENT occupied cells, so in a packed
panel two items that touch become one cluster. MEASURED on his own frame f_1788100004704.jpg:

    33 occupied cells  ->  2 clusters
       cluster 1: 25 of 33 cells, footprint 7x4   <- plainly many items, not one
       cluster 2:  8 cells,       footprint 2x4

Storing those under a name like "items" would be a label that outlived its referent, which is how
a right number ends up under a word that stopped being true. They are stored as `blobs`, with
`blobsAreItems: False` beside them. [[label-outlived-referent]] [[unknown-stays-unknown]]

THE SPLIT THIS LAW PINS:
    CELLS   reliable — derived count == the occupancy count, no inference in between
    BLOBS   a hint — coarse wherever items touch, never a tally of items
"""
import ast
import io
import os
import textwrap
import unittest

from console_safe import enable as _console_safe_enable

_console_safe_enable()

HERE = os.path.dirname(os.path.abspath(__file__))


def _glimpse_src():
    """The glimpse region, anchored at BOTH ends.

    ⚠ This used to be `src[i - 2600 : i + 1200]`, and adding a comment block above the region
    silently pushed the derivation out of the window — every law that reads it then reported the
    code ABSENT while it sat four lines higher. A fixed-size window measures the guess, not the
    file. [[source-window-shortcut]]
    """
    with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
        src = fh.read()
    a = src.find("_cells, _groups, _gwhy = [], [], \"\"")
    assert a > 0, "the cell derivation is gone — no start anchor"
    a = src.rfind("\n", 0, a) + 1      # to the START of its line, or dedent sees indent 0
    b = src.find("})", src.find("_glimpsed.append({", a))
    assert b > a, "the glimpse record is gone — no end anchor"
    return src[a:b + 2]


class TestABlobOfCellsIsNotAnItem(unittest.TestCase):

    def test_the_cells_are_carried_not_only_the_counts(self):
        seg = _glimpse_src()
        code = "\n".join(ln.split("#", 1)[0] for ln in seg.splitlines())
        for token in ('"cells"', '"cellsN"'):
            self.assertIn(token, code,
                          "the glimpse keeps only the counts again — the per-cell grid is the "
                          "whole point and it is computed either way")
        self.assertIn('_occ.get("grid")', code,
                      "nothing reads the grid, so the cells cannot have come from the pixels")
        print("glimpse carries: cells + cellsN, derived from _occ['grid']")

    def test_a_cluster_is_never_called_an_item(self):
        seg = _glimpse_src()
        code = "\n".join(ln.split("#", 1)[0] for ln in seg.splitlines())
        self.assertIn('"blobsAreItems": False', code,
                      "the clusters are stored without the flag that says they are not items")
        self.assertNotIn('"items"', code,
                         "a cluster of adjacent cells is being stored under the word ITEMS. "
                         "Measured on his own frame, one cluster held 25 of 33 cells with a 7x4 "
                         "footprint — that is many items, and the word would be a lie")
        print("clusters stored as blobs, with blobsAreItems=False")

    def test_adjacent_items_really_do_merge(self):
        """The measurement behind the caveat, with no footage — so it cannot go blind on CI."""
        import slot_identity as si
        # two 2x2 items sitting side by side with NO gap: 8 cells, 2 items
        packed = [(c, r) for c in range(4) for r in range(2)]
        groups, _why = si.item_groups(packed, "stash")
        print("8 cells of two touching 2x2 items -> %d cluster(s)" % len(groups or []))
        self.assertEqual(len(groups or []), 1,
                         "two touching items did NOT merge, so the caveat this law exists for "
                         "would be false and the wording must be revisited")
        # and with a one-cell gap they separate, which proves the grouping is real, not broken
        apart = [(c, r) for c in (0, 1, 5, 6) for r in range(2)]
        g2, _ = si.item_groups(apart, "stash")
        print("the same two items with a gap      -> %d cluster(s)" % len(g2 or []))
        self.assertEqual(len(g2 or []), 2,
                         "separated items did not separate — the grouping is broken, which is a "
                         "different defect from the coarseness this law describes")

    def test_a_footprint_carries_its_geometry(self):
        import slot_identity as si
        groups, _ = si.item_groups([(8, 0), (9, 0), (8, 1), (9, 1)], "stash")
        self.assertTrue(groups, "no cluster came back for four adjacent cells")
        g = groups[0]
        for k in ("col", "row", "w", "h"):
            self.assertIn(k, g, "a footprint with no %r cannot locate anything on the ledger" % k)
        print("footprint keys present: col/row/w/h -> %s"
              % {k: g.get(k) for k in ("col", "row", "w", "h")})

    def test_the_derivation_cannot_invent_a_cell(self):
        """The cells come from the grid alone — PARSED, not grepped.

        A law that reads source must parse it, because a string search cannot tell a real loop from
        the same characters inside a comment or a docstring. [[source-reading-guard]]
        """
        # the region is nested ~36 columns deep, so it must be DEDENTED before it will
        # parse; .strip() only reaches the first line and raises IndentationError.
        tree = ast.parse(textwrap.dedent(_glimpse_src()))
        # every value appended to _cells must be built from the loop variables the grid walk binds,
        # never from a range() or a literal count
        appends = [n for n in ast.walk(tree)
                   if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                   and n.func.attr == "append"
                   and isinstance(n.func.value, ast.Name) and n.func.value.id == "_cells"]
        self.assertTrue(appends, "nothing appends to _cells — the derivation is gone")
        for call in appends:
            for sub in ast.walk(call):
                if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name):
                    self.assertNotEqual(
                        sub.func.id, "range",
                        "a cell is being synthesised from range() — that invents occupancy the "
                        "pixels never reported")
        names = {n.id for call in appends for n in ast.walk(call) if isinstance(n, ast.Name)}
        self.assertTrue({"_ci", "_ri"} <= names,
                        "the appended cell does not use the grid walk's own indices (_ci/_ri); it "
                        "is coming from somewhere other than the pixels")
        print("cells parsed: %d append(s) to _cells, built from _ci/_ri, no range()" % len(appends))


    def test_the_container_is_the_panel_the_pixels_came_from(self):
        """⚠ THE SCREEN'S NAME IS NOT THE CELLS' CONTAINER.

        Every frame reaching the glimpse passed `stash_screen_open()`, so `surface` is very nearly
        always "stash". But the cells come from `inventory_occupancy`, which reads INV_CROP ->
        x 1749..2690 of 2940 — the INVENTORY panel. `panel_box_for("stash")` is at x 281..1149, a
        different region of the screen. Passing `surface` declared a 10x4 read to be a 10x10 grid.

        It fails SILENTLY, which is why it needs a law rather than a comment: item_groups filters
        cells to the container's bounds, and 4 rows fit inside 10, so nothing is dropped — every
        footprint just carries the wrong container forever.
        """
        seg = _glimpse_src()
        code = "\n".join(ln.split("#", 1)[0] for ln in seg.splitlines())
        self.assertIn('_cells], "inventory")', code,
                      "the container handed to item_groups is not the literal 'inventory' — if it "
                      "is `surface`, the FRAME's label is being stamped onto cells that live in a "
                      "different panel")
        self.assertNotIn('surface or "stash")', code,
                         "item_groups is being handed the screen's name again")
        import slot_identity as si
        self.assertEqual(si.GRIDS["inventory"], (10, 4),
                         "the inventory grid changed shape; this law's arithmetic below assumes 10x4")
        cols, rows = si.GRIDS["inventory"]
        print("container pinned to 'inventory' — GRIDS['inventory'] = %dx%d = %d cells "
              "(his frame read 33 occupied + 7 free = 40); stash would be %d"
              % (cols, rows, cols * rows, si.GRIDS["stash"][0] * si.GRIDS["stash"][1]))
        self.assertEqual(cols * rows, 40,
                         "the read that motivated this law returned 40 cells, which is what "
                         "identified the panel as the inventory in the first place")


RED_PROOF = [
    {
        "why": "the glimpse goes back to keeping only the counts, so the per-cell grid is thrown "
               "away again and the ledger can never say where in the panel anything sat — the "
               "exact one-line loss this whole join exists to undo",
        "file": "control_app.py",
        "find": '                                        "cells": _cells,',
        "replace": '                                        "cellsREMOVED": None,',
        "matches": 1,
    },
    {
        "why": "the clusters lose the flag that says they are not items, so a 7x4 blob holding 25 "
               "of 33 cells can be read as one item and tallied as one",
        "file": "control_app.py",
        "find": '                                        "blobsAreItems": False,',
        "replace": '                                        "blobsAreItems": True,',
        "matches": 1,
    },
    {
        "why": "the container goes back to the SCREEN's name, so cells read out of the inventory "
               "panel are declared to be a 10x10 stash grid - the frame-label-as-item-location "
               "defect, silent because 4 rows fit inside 10 and nothing is dropped",
        "file": "control_app.py",
        "find": '                                            [(c, r) for c, r in _cells], "inventory")',
        "replace": '                                            [(c, r) for c, r in _cells], surface or "stash")',
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
