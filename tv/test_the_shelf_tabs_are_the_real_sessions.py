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
        """⚠ v3214 — TWO BRANCHES NOW, BECAUSE AN EMPTY BAR WAS HIDING TWO OPPOSITE FACTS.

        The original assertion was the literal text `if (!seen.length) { bar.hidden = true;`,
        which pinned the FORMATTING of one line rather than the behaviour. It was right that a
        bar with nothing stamped must not read as "no stations exist" — but `bar.hidden = true`
        fired in two situations that are not the same:

          · the river has not answered yet            -> hiding is correct, the header says so
          · the river HAS answered and no card is stamped -> that is a DEFECT, and hiding buried it

        The second is the unjoined end #227 named: the strip above prints station counts from
        /api/river while the grid beside it carries none. So this now pins BOTH branches, and
        does it on structure rather than on a byte sequence any reformat would break.
        [[zero-needs-a-denominator]] [[the-unjoined-end]] [[source-reading-guard]]
        """
        self.assertIn("if (!seen.length)", self.fn,
                      "nothing branches on an unstamped shelf at all, so a bar with no chips "
                      "renders empty and reads as 'no stations exist'")
        # ⚠⚠ THE BRANCH ITSELF, BY BRACE COUNTING — NOT A FIXED WINDOW OF CHARACTERS.
        # A `[:1400]` slice ran past the end of this branch into the chip builder below, where
        # `SHELF_RIVER_ORDER` and `SHELF_RIVER_LABELS` both CONTAIN the substring "SHELF_RIVER".
        # A sabotage that deleted the river consultation outright stayed GREEN, because the
        # assertion was being satisfied by two unrelated identifiers further down — which is the
        # exact failure the test three below this one already records ("a guard a rename satisfies
        # is measuring the alphabet"). Anchor BOTH ends or the reach is the finding.
        # [[source-reading-guard]] [[sabotage-is-usually-the-wrong-one]]
        _i = self.fn.index("if (!seen.length)")
        _o = self.fn.index("{", _i)
        _d, _j = 0, _o
        while _j < len(self.fn):
            if self.fn[_j] == "{":
                _d += 1
            elif self.fn[_j] == "}":
                _d -= 1
                if _d == 0:
                    break
            _j += 1
        tail = self.fn[_o:_j + 1]
        self.assertLess(len(tail), 1400,
                        "the unstamped branch is %d chars — too large to be the branch, so this "
                        "is reading past it again" % len(tail))
        self.assertIn("bar.hidden = true", tail,
                      "an unstamped shelf no longer hides the bar, so an empty chip row is shown "
                      "as though the river had answered with nothing")
        self.assertIn("Object.keys(SHELF_RIVER", tail,
                      "the empty branch does not consult the river, so it cannot tell 'not "
                      "answered yet' from 'answered, and not one card is stamped' — and those "
                      "are opposite facts")
        self.assertIn("bar.hidden = false", tail,
                      "there is no branch that SHOWS the bar when the river answered and no card "
                      "carries a stamp, so the river-vs-grid mismatch stays invisible")

    def test_the_count_says_what_it_is_OVER(self):
        """[[zero-needs-a-denominator]] — a bare number on a chip is a figure with no scale."""
        self.assertIn("' of the ' + total + ' stamped reel(s)", self.fn,
                      "the chip tooltip gives a count with no denominator")

    def test_a_TRAJECTORY_is_never_claimed_from_an_OCCUPANCY_count(self):
        """★ HIS SHELF, READ BACK TO ME OFF ITS OWN TOOLTIP: *"no reel has reached triage yet"*,
        *"no join has reached yet also"* - and then the real report, *"it just looks stuck this
        way and as if the river IS not flowing"*.

        MEASURED the same minute on his live river:
            counts (WHERE THEY SIT)   TRIAGE 2 - JOIN 14 - CAPTURE 21 - ROUTED 21
            visits (WHO PASSED THROUGH) TRIAGE 21 - JOIN 14 - ROUTED 33
        21 reels have been through TRIAGE and the chip said NO REEL HAS REACHED IT. The count is
        an OCCUPANCY and the sentence was a TRAJECTORY, and `one_funnel.py` already carries this
        exact scar in its own gotcha - *"'no reel sits at banked' and 'no reel ever passed banked'
        are opposite"* - carved on a neighbouring module while this surface committed it verbatim.

        The law pins the JOINT, not the wording: an empty chip may not make an ever-claim unless
        it consulted something that actually knows. [[the-unjoined-end]] [[label-outlived-referent]]
        """
        self.assertNotIn("NO reel has reached", self.fn,
                         "the chip is claiming a reel has never REACHED a station from a count of "
                         "what sits there NOW - opposite facts, and his river has passed 21 reels "
                         "through the station it called untouched")
        self.assertIn("SHELF_RIVER_VISITS", self.fn,
                      "the builder never consults the river's visits, so it has nothing to answer "
                      "'has anything ever been here' with and can only guess from occupancy")
        self.assertIn("SHELF_RIVER_UNREACHED", self.fn,
                      "the builder never consults the river's own unreached list")

    def test_an_UNREPORTED_trajectory_stays_UNKNOWN(self):
        """⚠ THE DANGEROUS DIRECTION. A river that answers WITHOUT `visits` must not let the chip
        fall back to "never" - that is the same fabrication in the other direction, and it would
        be invisible because it reads exactly like a measured zero. [[unknown-stays-unknown]]"""
        self.assertIn("UNKNOWN", self.fn,
                      "no branch says UNKNOWN, so a river that reported no visits is presented as "
                      "a river that reported zero")
        self.assertIn("=== 'number'", self.fn,
                      "the visits read is not type-checked, so a missing key becomes undefined and "
                      "compares as a number would not")

    def test_the_REMAINDER_is_counted_even_when_stations_are_stamped(self):
        """★ HIS SCREENSHOT: the chips summed to 12 and the header said "13 of 13". One card sat
        in no chip at all - not even UNKNOWN - and nothing accounted for it.

        The accounting existed, and ONLY inside the `!seen.length` branch: it ran only when NOTHING
        was stamped. The moment one station held a reel - the case where a missing card is hardest
        to spot - it stopped counting. A denominator that appears only when the numerator is zero
        is not a denominator. [[zero-needs-a-denominator]]
        """
        i = self.fn.find("var total = 0;")
        j = self.fn.find("bar.hidden = false;", i)
        self.assertGreater(i, -1, "the total is gone; re-anchor this law")
        self.assertGreater(j, i, "the show-the-bar line is gone; re-anchor this law")
        main = self.fn[i:j]
        self.assertIn("data-station-why", main,
                      "the stamped path does not account for cards carrying no station, so a card "
                      "in no chip vanishes from a row whose numbers are supposed to close")
        # ⚠ THE PRINT MUST BE REACHABLE, not merely present. A first cut of this law asserted
        # only that the class appears somewhere in the branch, which an `if (false)` around the
        # print would have satisfied perfectly - the remainder computed, then thrown away, which
        # is the historical behaviour this law exists to refuse. So it is anchored to the GUARD.
        g = main.find("if (_rmWithheld || _rmNoStamp)")
        self.assertGreater(g, -1,
                           "the remainder has no live guard, so it is computed and never shown - "
                           "which is the state his screenshot was in")
        self.assertIn("sh-chip-strem", main[g:g + 1600],
                      "nothing PRINTS the remainder inside its own guard, so it is counted and "
                      "then thrown away")

    def test_the_denominator_cannot_be_NaN(self):
        """★ IT WAS. Found by RENDERING the shipped chip and reading its tooltip off his live
        console: *"7 of the NaN stamped reel(s)"*.

        `ordered` carries every station the river names; `tally` only the ones some card is at. So
        the first ordered station with no cards made the sum `0 + undefined`, and every chip after
        it printed NaN as its denominator. The sibling law above asserts the PHRASE
        "of the N stamped reel(s)" is present - and NaN satisfies that phrase perfectly, which is
        why it went unseen. A number printed as NaN is a missing denominator wearing a figure.
        [[zero-needs-a-denominator]] [[regression-guard]]
        """
        self.assertIn("total += (tally[st] || 0)", self.fn,
                      "the chip total sums tally entries without guarding the stations that have "
                      "no cards, so the denominator is NaN again")

    def test_an_empty_SHELF_chip_does_not_claim_an_empty_RIVER(self):
        """⚠ THE CONTRADICTION THE FIRST CUT SHIPPED, caught on real pixels before it went out:
        JOIN carried the DAM mark and its own sentence said *"the river flows here, it is simply
        not holding anything"* - while the river held 14 reels at JOIN with none ever leaving.

        The shelf window is 13 cards; the river is 63 reels. A chip that is empty in the WINDOW
        must consult the RIVER's occupancy before saying anything about the river.
        """
        self.assertIn("SHELF_RIVER_COUNTS", self.fn,
                      "the builder never reads the river's own occupancy, so it can only describe "
                      "the 13-card window while appearing to describe the river")
        # ⚠⚠ AND SOMETHING MUST WRITE IT. A sabotage that renamed the ASSIGNMENT left this law
        # green, because the law only ever asked whether the BUILDER reads the variable - and it
        # still did, from a name nothing sets. The read would then be null for ever and every
        # river sentence would quietly degrade to the window-only branch, which is the exact
        # defect this file exists to catch, one level up. Both ends, or neither.
        # [[the-unjoined-end]] [[sabotage-is-usually-the-wrong-one]]
        self.assertIn("SHELF_RIVER_COUNTS = (d.counts", self.code,
                      "nothing ASSIGNS SHELF_RIVER_COUNTS from the river payload, so the builder "
                      "reads a name that is null for ever and silently falls back to the "
                      "shelf-window sentence")
        i = self.fn.find("} else if (rHere > 0) {")
        self.assertGreater(i, -1,
                           "there is no branch for 'empty on this shelf, occupied in the river' - "
                           "so that state falls through to a sentence about flow")
        self.assertIn("THIS SHELF", self.fn[i:i + 700],
                      "that branch does not name WHICH population is empty")

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
