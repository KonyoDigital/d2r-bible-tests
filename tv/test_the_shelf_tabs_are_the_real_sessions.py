# -*- coding: utf-8 -*-
"""THE TABS ON TOP OF THE SHELF ARE BUILT FROM HIS REELS, NOT FROM A LIST.

He said it three times, escalating, because it kept not being done:
    "the tabs ontop need updating related to the reels sessions.. not random or outdated like it is"
    "and accorindgly relevant to the sessions"
    "the tabs within shelf on top need a fixing and updating so they represent the real reel
     sessions that its managing"

⚠⚠ AND THE FIRST TIME IT WAS "DONE" IT WAS HALF-DONE, BY ME. v3195 shipped `SHELF_F.station`, the
`st:` toggle branch, the filter clause in the predicate and the `active` flag — every half except
THE BUTTONS. So a complete, working filter sat in the file with nothing on screen able to reach
it. [[plumbing-with-no-tap]] in its purest form: both ends built, never joined, and it looked
finished from the code side.

THE RULES THIS PINS, each of which is what "not random or outdated" actually means:
  1. EVERY CHIP IS EARNED BY A CARD. The row is tallied from `data-station` on the visible cards,
     so a station with no reel gets no chip and the row can never show a stage his footage is not
     in.
  2. THE ORDER COMES FROM THE RIVER. `SHELF_RIVER_ORDER` is /api/river's own station sequence.
     This file already carries that ruling beside the sort selector — *"The station order is NEVER
     hardcoded here ... Two lists of stations is how they drift."* A hardcoded order would also
     silently drop any station reel_router gains. [[copy-drift]]
  3. AN UNMAPPED STATION IS MARKED, NEVER DROPPED. A stage the river order does not name is a
     finding about the router; hiding it makes the row lie by omission.
  4. AN EMPTY ROW HIDES ITSELF. Nothing stamped means the river has not answered — not that no
     stations exist. [[zero-needs-a-denominator]]
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

UI = os.path.join(HERE, "control_ui.html")


def _py_only(src):
    """`#`-style and `//` comment lines out, block comments out — but NOT triple-quoted spans.

    ⚠ A "strip docstrings" filter would delete real code here, the way it deleted render_check's
    browser probe when this helper was first written elsewhere. Only comment syntax goes.
    """
    src = re.sub(r"/\*.*?\*/", " ", src, flags=re.S)
    return re.sub(r"(?m)^\s*//.*$", " ", src)


def _between(src, start, end):
    i = src.find(start)
    if i < 0:
        return ""
    j = src.find(end, i + len(start))
    return src[i:j] if j > i else ""


class TheShelfTabsAreTheRealSessions(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with io.open(UI, encoding="utf-8") as fh:
            cls.src = fh.read()
        cls.code = _py_only(cls.src)
        cls.fn = _between(cls.code, "function _shStationChips(cards){",
                          "window._shStationChips")
        assert cls.fn, "_shStationChips is gone — this law is reading nothing"

    # ── the half that was missing for a whole version ────────────────────────────────────
    def test_the_buttons_actually_EXIST(self):
        """v3195's defect, pinned: a filter with no control is not a feature."""
        self.assertIn('id="sh-stationbar"', self.code,
                      "the station chip row has no container in the markup")
        self.assertIn("class=\"sh-chip sh-chip-st", self.fn,
                      "the builder emits no chip buttons")

    def test_the_builder_is_actually_CALLED(self):
        """[[the-unjoined-end]] — a builder nobody calls renders nothing, which is exactly the
        state this law exists to end."""
        self.assertIn("_shStationChips(vis)", self.code,
                      "nothing calls _shStationChips, so the row stays empty forever")

    def test_the_filter_half_is_still_wired(self):
        """both halves, or it is the same defect facing the other way."""
        self.assertIn("SHELF_F.station", self.code, "the station filter state is gone")
        self.assertIn("'st:'", self.code + repr(self.code),
                      "the st: toggle prefix is gone, so a chip click does nothing")
        self.assertIn("data-station", self.code, "the cards no longer carry their station")

    # ── what "not random or outdated" means, as assertions ───────────────────────────────
    def test_every_chip_is_earned_by_a_CARD(self):
        self.assertIn("getAttribute('data-station')", self.fn,
                      "the chips are no longer tallied from the cards, so the row can show a "
                      "station none of his reels is in — which is what he called random")
        self.assertIn("if (!st) return;", self.fn,
                      "an unstamped card is being counted into some station")

    def test_the_order_comes_from_the_RIVER_not_a_list_here(self):
        self.assertIn("SHELF_RIVER_ORDER", self.fn,
                      "the station order is no longer taken from /api/river — two lists of "
                      "stations is how they drift, and this file already carved that rule")
        # a literal station roster written into the builder is the exact thing being banned
        for banned in ("'INTAKE'", "'PRINTER'", "'CAPTURE'", "'TOMBSTONE'"):
            self.assertNotIn(banned, self.fn,
                             "a station name is hardcoded in the chip builder (%s) — that is a "
                             "second roster and it will drift from the router" % banned)

    def test_an_unmapped_station_is_MARKED_not_dropped(self):
        self.assertIn("sh-chip-stunk", self.fn,
                      "a station the river order does not name is silently dropped, so the row "
                      "lies by omission about a stage that has real reels in it")
        self.assertIn("indexOf(st) < 0", self.fn,
                      "nothing detects a station missing from the river order")

    def test_an_empty_row_HIDES_itself(self):
        self.assertIn("if (!seen.length) { bar.hidden = true;", self.fn,
                      "with nothing stamped the bar renders empty, which reads as 'no stations "
                      "exist' when the truth is that the river has not answered")

    def test_the_count_says_what_it_is_OVER(self):
        """[[zero-needs-a-denominator]] — a bare number on a chip is a figure with no scale."""
        self.assertIn("' of the ' + total + ' stamped reel(s)", self.fn,
                      "the chip tooltip gives a count with no denominator")

    # ── a class nobody styles is a flag nobody can see ───────────────────────────────────
    def test_every_class_the_BUILDER_EMITS_is_actually_styled(self):
        """The join, asked in the only direction that cannot be faked.

        ⚠⚠ TWO EARLIER CUTS OF THIS TEST WERE SATISFIED BY THINGS THAT WERE NOT THE POINT, and
        the red-proof caught both:
          1. `assertIn(".sh-chip.sh-chip-stunk", src)` — a sabotage renaming the rule to
             `...-stunkX` STAYED GREEN, because the renamed selector still CONTAINS the old one.
             A guard a rename satisfies is measuring the alphabet.
          2. Adding a `(?![\w-])` boundary fixed that and it STILL stayed green, because the
             class has TWO rules (`.sh-chip-stunk` and `.sh-chip-stunk::after`) and renaming one
             leaves the other.
        Both failures share a cause: the test asserted a STRING EXISTS rather than that the two
        halves AGREE. So it now reads the class names out of the builder itself and requires each
        to be styled. Rename it in either half and they stop matching, which is the actual defect.
        [[the-unjoined-end]] [[sabotage-is-usually-the-wrong-one]] [[source-reading-guard]]
        """
        emitted = set()
        for m in re.finditer(r"class=\\?\"([^\"]*sh-chip[^\"]*)", self.fn):
            for tok in re.split(r"[\s'+]+", m.group(1)):
                tok = tok.strip()
                if tok.startswith("sh-chip-"):
                    emitted.add(tok)
        print("   classes the builder emits: %s" % sorted(emitted))
        self.assertTrue(emitted,
                        "no sh-chip-* class could be read out of the builder, so this test is "
                        "checking nothing [[zero-needs-a-denominator]]")
        unstyled = [c for c in sorted(emitted)
                    if not re.search(r"\." + re.escape(c) + r"(?![\w-])", self.src)]
        self.assertEqual([], unstyled,
                         "the builder emits %r and the stylesheet never styles it — a class "
                         "nobody styles is a flag nobody can see, the same "
                         "[[plumbing-with-no-tap]] shape as the buttons that were missing"
                         % unstyled)


RED_PROOF = [
    ("control_ui.html", "_shStationChips(vis)", "_shStationChipsX(vis)",
     "test_the_builder_is_actually_CALLED"),
    ("control_ui.html", 'id="sh-stationbar"', 'id="sh-stationbarX"',
     "test_the_buttons_actually_EXIST"),
    # tamper the BUILDER, which is the half that decides what must be styled
    ("control_ui.html", "class=\"sh-chip sh-chip-st'", "class=\"sh-chip sh-chip-stZ'",
     "test_every_class_the_BUILDER_EMITS_is_actually_styled"),
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
