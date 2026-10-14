#!/usr/bin/env python3
"""A KAI judge row names the panel the tooltip sat on.

The 8% area floor was measured at 2560x1665, where a real tooltip is 33% of the
frame and the HUD impostor is 2.8%. At 1440x936 the same finder reports a
legible tooltip as one or two tiles of the 6x6 sweep — 2.8% or 5.6% — and 8%
refused 4 of 4 Session-1 frames. The floor scales with the capture so that
cluster is admitted, and the calibration-size HUD stays refused.

The compile then joins the rect to a panel and writes names_loc on the kai row:
the left panel is the stash, the right panel is 'on him' (inventory, slot
unknown), and a tooltip that was not located stays None.
"""
import os
import sys
import tempfile
import unittest

import fixture_tmp as _fx_tmp  # noqa: E402  # this run's scratch dirs leave with it
_fx_tmp.contain()

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

# The compile reads CONTROL_PORT at import. Point it off his live console.
os.environ.setdefault("TV_CONTROL_PORT", "9")

import tooltip_find as TF  # noqa: E402
import control_app as ca  # noqa: E402


def _frame(w, h):
    """A real image. locate() opens the file before it asks the reader."""
    from PIL import Image
    d = tempfile.mkdtemp()
    p = os.path.join(d, "frame.jpg")
    Image.new("RGB", (w, h), (12, 10, 8)).save(p, "JPEG", quality=60)
    return p


def _fake(grid):
    """N text lines per tile, in the order density() visits them."""
    state = {"i": 0}
    flat = [n for row in grid for n in row]

    def read(_path):
        n = flat[state["i"]] if state["i"] < len(flat) else 0
        state["i"] += 1
        return {"lines": ["a line of text"] * n}
    return read


def _grid(rows, cols, cells):
    g = [[0] * cols for _ in range(rows)]
    for (r, c), n in cells.items():
        g[r][c] = n
    return g


def _kai(extra):
    row = {
        "lane": "kai", "ts": 100, "captureTs": 100,
        "frameId": "f_fixture", "sessionId": "s_fixture",
        "scene": "kai",
        "kai": {"judge": {"name": "Windforce", "tier": "grail", "score": 9}},
    }
    row.update(extra)
    return row


def _loc(row):
    reg = {r["name"]: r for r in ca._kai_compile_register([row])}
    return (row.get("names_loc") or {}).get("Windforce"), (reg.get("Windforce") or {}).get("loc")


class TestTheFloorScalesWithTheCapture(unittest.TestCase):
    """One tile of a 6x6 sweep is 2.8% of any frame. At 1440x936 that is a tooltip.
    At 2560x1665 it is the HUD, and 8% still refuses it."""

    def test_a_one_tile_and_a_two_tile_cluster_at_1440x936_are_admitted(self):
        # The Session-1 measurement: densest text 2.8% (one tile) and 5.6% (two).
        # Both sit under the fixed 8% floor.
        one = _grid(6, 6, {(1, 4): 8})
        rect, why = TF.locate(_frame(1440, 936), reader=_fake(one))
        self.assertIsNotNone(rect, why)
        frac = float(rect[2] * rect[3]) / float(1440 * 936)
        self.assertLess(frac, 0.08, "this cluster is not the one 8%% used to refuse")
        self.assertGreater(frac, 0.02, "a speck was admitted")

        two = _grid(6, 6, {(2, 0): 6, (2, 1): 6})
        rect2, why2 = TF.locate(_frame(1440, 936), reader=_fake(two))
        self.assertIsNotNone(rect2, why2)
        frac2 = float(rect2[2] * rect2[3]) / float(1440 * 936)
        self.assertLess(frac2, 0.08)
        self.assertGreater(frac2, frac)

    def test_the_calibration_hud_is_still_refused(self):
        # (2450, 0, 490, 318) on a 2560-wide frame — one corner tile, 2.8%.
        hud = _grid(6, 6, {(0, 5): 40})
        rect, why = TF.locate(_frame(2560, 1665), reader=_fake(hud))
        self.assertIsNone(rect, "the HUD box at the calibration size was accepted")
        self.assertIn("chrome", why or "")


class TestTheCompileJoinsTheRectToThePanel(unittest.TestCase):

    def test_left_is_stash_right_is_on_him_and_missing_is_none(self):
        left = _kai({"tooltipRect": (40, 180, 380, 420), "frameW": 1440, "frameH": 936})
        self.assertEqual(_loc(left), ("stash", "stash"))

        right = _kai({"tooltipRect": (900, 80, 420, 360), "frameW": 1440, "frameH": 936})
        self.assertEqual(_loc(right), ("on him", "on him"))

        absent = _kai({})
        self.assertEqual(_loc(absent), (None, None))

        # A rect that covers both panels equally is not a guess.
        split = _kai({"tooltipRect": (520, 100, 400, 300), "frameW": 1440, "frameH": 936})
        self.assertEqual(_loc(split), (None, None))

        # A place the row already stated is the better witness.
        kept = _kai({
            "names_loc": {"Windforce": "equipped"},
            "tooltipRect": (40, 180, 380, 420), "frameW": 1440, "frameH": 936,
        })
        self.assertEqual(_loc(kept), ("equipped", "equipped"))

    def test_the_compile_locates_the_frame_it_was_handed(self):
        # The real locate(), on the 1440 fixture, through the real compile.
        # One tile on the right: under 8% of the frame, and on him.
        frame = _frame(1440, 936)
        row = _kai({
            "framePath": frame,
            "tooltipReader": _fake(_grid(6, 6, {(1, 4): 8})),
        })
        self.assertEqual(_loc(row), ("on him", "on him"))


if __name__ == "__main__":
    try:
        import console_safe as _cs
        _cs.enable()
    except Exception:
        pass
    unittest.main(verbosity=1)
