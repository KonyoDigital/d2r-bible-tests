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
    """⚠⚠ #123 — v3379 gave the no-window path a DISK fallback (the board's banked hand-over store), and
    this law went on asserting "no window -> None". On his Mac the store exists, so his REAL board came
    back (`have: 312`) and the gate sat red in every census, UNPROVABLE; on CI there is no store and it
    stayed green. A law whose verdict was the venue — and a fixture reading his live board. The store is
    now STUBBED in every case and both branches of the fallback are pinned.
    [[feedback-fixtures-never-touch-live-data]] [[label-outlived-referent]]"""

    def setUp(self):
        self._store = CA._mask_from_board_store
        self._wins = dict((k, CA.__dict__[k]) for k in ("_BOARD_WIN", "_MAIN_WIN") if k in CA.__dict__)
        CA._BOARD_WIN = None
        CA._MAIN_WIN = None
        self.asked = []

    def tearDown(self):
        CA._mask_from_board_store = self._store
        for k in ("_BOARD_WIN", "_MAIN_WIN"):
            if k in self._wins:
                setattr(CA, k, self._wins[k])
            else:
                CA.__dict__.pop(k, None)

    def _stub(self, answer):
        def _fake(ledger="sets"):
            self.asked.append(ledger)
            return answer
        CA._mask_from_board_store = _fake

    def test_no_window_and_no_store_is_None_and_names_BOTH_links(self):
        self._stub((None, "no store handed over"))
        CA._MASK_WHY["uniques"] = None
        got = CA.board_mask("uniques")
        self.assertIsNone(got, "nothing could be read and a dict was published anyway")
        why = (CA._MASK_WHY.get("uniques") or "").lower()
        self.assertIn("window", why, "the window link that refused first is not named: %r" % why)
        self.assertIn("handed", why, "the store link that refused second is not named: %r" % why)
        self.assertEqual(self.asked, ["uniques"], "premise: the fallback never asked the store")

    def test_no_window_but_a_BANKED_store_is_that_stores_mask(self):
        """v3379's own point: a console with no window publishes the list the board handed over."""
        fake = {"v": "fixture", "n": 3, "b": "abc", "have": 2}
        self._stub((fake, ""))
        got = CA.board_mask("uniques")
        self.assertEqual(got, fake, "a banked store was available and the mask was dropped")
        self.assertIsNone(CA._MASK_WHY.get("uniques"), "a mask that arrived still carries a why")

    def test_unknown_ledger_is_None_not_a_sets_mask(self):
        self._stub((None, "no store handed over"))
        got = CA.board_mask("no-such-ledger")
        self.assertIsNone(got)
        why = CA._MASK_WHY.get("no-such-ledger")
        self.assertTrue(why, "an unknown ledger must name itself, not silently become sets")
        self.assertIn("ledger", why.lower())

    def test_a_failure_dict_must_not_be_what_the_wire_would_keep(self):
        """`if m:` on `{ok: False, why: ...}` is True. That is the shape this must never return."""
        self._stub((None, "no store handed over"))
        got = CA.board_mask("uniques")
        self.assertFalse(isinstance(got, dict) and got.get("ok") is False)


class FleetXrefUsesTheBoardResolver(unittest.TestCase):
    """N-2 — rarity from `_artRarity(n)` (the KEY), display from `_pieceLabel(n)`."""

    def test_the_tile_asks_artRarity_with_the_key_not_the_stripped_name(self):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "control_ui.html")
        with open(path, encoding="utf-8") as fh:
            ui = fh.read()
        i = ui.find("var tile = function (n, side)")
        self.assertGreater(i, 0)
        blk = ui[i:ui.find("var col = function", i)]
        self.assertIn("_artRarity(n)", blk)
        self.assertNotIn("_artRarity(bare)", blk)
        self.assertIn("_pieceLabel(n)", blk)
        self.assertIn("name: n", blk)




# ══ THE EXECUTABLE RED-PROOF ═════════════════════════════════════════════════
# PROPOSED by tv/heart2_candidates.py — derived from this gate's OWN assertions and
# measured against the target file (each anchor occurs exactly once). Review it: the
# question is whether deleting this text is the defect the law exists to catch.
RED_PROOF = [
    {
        "why": 'the law requires this text in control_ui.html; deleting it must turn the gate red',
        "file": 'control_ui.html',
        "find": '_w._artRarity(n) || rar',
        "replace": '_HEART2_TAMPERED_',
        "matches": 1,
    },
    {
        "why": 'the law requires this text in control_ui.html; deleting it must turn the gate red',
        "file": 'control_ui.html',
        "find": '_pieceLabel(n)',
        "replace": '_HEART2_TAMPERED_',
        "matches": 1,
    },
    {
        "why": "#123 - the banked-store fallback dropped: a console with no window publishes no list again, the v3379 report exactly",
        "file": "control_app.py",
        "find": "    if m:\n        _MASK_WHY[key] = None\n        return m",
        "replace": "    if False:\n        _MASK_WHY[key] = None\n        return m",
        "matches": 1
    },
    {
        "why": "#123 - the why keeps only the SECOND refusal, hiding that the window path was tried and why it refused",
        "file": "control_app.py",
        "find": "    _MASK_WHY[key] = (\"%s; and the board has not handed its stores over either (%s)\"\n                      % (live, bwhy or \"no reason given\"))[:400]",
        "replace": "    _MASK_WHY[key] = (\"the board has not handed its stores over (%s)\"\n                      % (bwhy or \"no reason given\"))[:400]",
        "matches": 1
    },
]

if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
