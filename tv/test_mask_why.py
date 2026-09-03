"""N-3 — a mask that cannot be built must say WHICH link gave up.

⚠ Returning a failure dict would PUBLISH it (`if m:` is True). None stays omitted.
The why rides in `_MASK_WHY`, never as a zero mask. [[unknown-stays-unknown]]
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import control_app as CA


class AMissingMaskNamesTheLink(unittest.TestCase):

    def test_no_window_is_None_and_names_the_window(self):
        CA._MASK_WHY["uniques"] = None
        got = CA.board_mask("uniques")
        self.assertIsNone(got, "a missing window must omit the mask, not publish a dict")
        why = CA._MASK_WHY.get("uniques")
        self.assertTrue(why, "the why was collapsed to None with the mask")
        self.assertIn("window", why.lower())

    def test_unknown_ledger_is_None_not_a_sets_mask(self):
        got = CA.board_mask("no-such-ledger")
        self.assertIsNone(got)
        why = CA._MASK_WHY.get("no-such-ledger")
        self.assertTrue(why, "an unknown ledger must name itself, not silently become sets")
        self.assertIn("ledger", why.lower())

    def test_a_failure_dict_must_not_be_what_the_wire_would_keep(self):
        """`if m:` on `{ok: False, why: ...}` is True. That is the shape this must never return."""
        got = CA.board_mask("uniques")
        self.assertFalse(isinstance(got, dict) and got.get("ok") is False)


class FleetXrefUsesTheBoardResolver(unittest.TestCase):
    """N-2 — rarity from `_artRarity(n)` (the KEY), display from `_pieceLabel(n)`."""

    def test_the_tile_asks_artRarity_with_the_key_not_the_stripped_name(self):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "control_ui.html")
        with open(path, encoding="utf-8") as fh:
            ui = fh.read()
        i = ui.find("var tile = function (n, mine)")
        self.assertGreater(i, 0)
        blk = ui[i:ui.find("var col = function", i)]
        self.assertIn("_artRarity(n)", blk)
        self.assertNotIn("_artRarity(bare)", blk)
        self.assertIn("_pieceLabel(n)", blk)
        self.assertIn("name: n", blk)


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
