#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v2819 (#43) — TWO SURFACES, TWO SOURCES, AND NEITHER SAID WHICH.

THE SHELF stacks two "flow" strips in one overlay, deliberately styled to read as one engine.
MEASURED 2026-09-09 — they are drawn from different modules with different vocabularies:

    #sh-lanes    _shLanesRender   /api/river       river_lanes + reel_router   4 lanes / 9 stations
    .shp-spine   _shStoryRender   /api/reel_story  printer.stream()            7 stations

Both use the word PRINTER and mean different things: in the first it is ONE router station holding
N reels; in the second it is a seven-step internal pipeline. The join happens at the endpoint layer,
for display only — so a reel's router-station and its printer-station can diverge and neither
surface flags it. That seam is #36 seen from the UI side.

⚠ AND THE HOUSE ALREADY HAD THE CONVENTION. `.ftt-age "as of …"` labels freshness on the fleet
tooltip in this same file. Measured: 3 "as of" hits in the whole file, NONE in the shelf code. The
pattern existed and these two surfaces simply did not use it.

★ THE JOIN IS THE LAW, NOT THE STRING. The first cut of this fix BUILT `_srcTag` and never rendered
it — a label living in a variable is the same as no label. Caught before shipping only by going
looking for the join, which is why the gate below asserts the tag is USED and not merely present.
[[the-unjoined-end]] [[stale-reading]]
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import source_window as _sw  # noqa: E402

UI = os.path.join(HERE, "control_ui.html")


def _ui():
    with io.open(UI, encoding="utf-8") as fh:
        return fh.read()


class TestEachFlowStripNamesItsOwnEngine(unittest.TestCase):

    def setUp(self):
        self.src = _ui()

    def test_the_river_strip_names_the_router(self):
        head = _sw.between(self.src, 'var H = [\'<div class="shr-head">', "'<div class=\"shr-flow\">'",
                           what="the river strip's header")
        self.assertIn("shr-src", head,
                      "the river strip carries no source tag, so a reader cannot tell which engine "
                      "produced its counts — and the strip below it counts in a different "
                      "vocabulary under the same word PRINTER")
        self.assertIn("router", head,
                      "the tag does not name the router as its source")

    def test_the_printer_spine_names_the_printer(self):
        block = _sw.between(self.src, "var _srcTag =", "var cells = st.printerStations.map",
                            what="the printer spine's source tag")
        self.assertIn("printer", block.lower(),
                      "the spine's tag does not name printer.stream() as its source")
        self.assertIn("/api/reel_story", block,
                      "the tag does not name the endpoint, so the two strips still cannot be told "
                      "apart by anyone reading the screen")

    def test_the_tag_is_RENDERED_not_merely_BUILT(self):
        """★ THE ONE THAT NEARLY SHIPPED WRONG. A source label assigned to a variable and never
        placed in the markup is exactly as useful as no label at all."""
        built = self.src.count("var _srcTag")
        used = self.src.count("+ _srcTag") + self.src.count("_srcTag +")
        self.assertEqual(built, 1, "expected exactly one _srcTag definition, found %d" % built)
        self.assertGreater(used, 0,
                           "_srcTag is BUILT (%d) and never concatenated into any markup — the "
                           "label exists in a variable and never reaches the screen" % built)

    def test_both_tags_have_a_style_or_they_are_invisible(self):
        """A tag with no rule is a tag nobody sees — naming the container is not naming the rule."""
        self.assertIn(".shr-src", self.src,
                      "no CSS rule for .shr-src, so the source tags inherit whatever surrounds "
                      "them and may not be legible at all")


# ══ THE EXECUTABLE RED-PROOF ═════════════════════════════════════════════════════════════════
RED_PROOF = [
    {
        "why": "un-rendering the tag is the exact near-miss — BUILT and never placed in the markup",
        "file": "control_ui.html",
        "find": "      _spine = '<div class=\"shp-head\">' + _srcTag + '</div>'",
        "replace": "      _spine = ''",
        "matches": 1,
    },
    {
        "why": "removing the river strip's tag returns it to a count with no engine named",
        "file": "control_ui.html",
        "find": "             + '<span class=\"shr-src\" title=\"4 lanes over reel_router\\u2019s 9 stations, from /api/river\">'",
        "replace": "             + '<span class=\"gone\" title=\"\">'",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
