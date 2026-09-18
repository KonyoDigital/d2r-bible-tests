# -*- coding: utf-8 -*-
"""v3293 — THE EAGLE'S THREE FIGURES MUST COUNT THE POPULATION THE PANEL DRAWS.

Grok Bot's native eyes, LOOKED #5724880074 on v3291:

    "CHILIAD: YOU 10 / CODE 1 / not measured 23 (panel 23-vs-25 disagree)"

⚠ THAT SENTENCE IS v3284 WORKING. The clause exists to refuse two numbers sitting side by side in
silence, and it caught a real defect underneath — which is the only reason this file exists.

TWO INDEPENDENT DIVERGENCES, both making the panel draw MORE than the figures admitted:

  1. ONE SPELLING vs TWO. control_app counted `state == "unknown"`; control_ui.html:12787 buckets
     `'unknown' || 'unmeasured'`. console_doctor emits UNMEASURED for a SLOW check that has never
     had a full pass, so any board without one carries rows the counter never saw.
  2. A WHOLE LIST. `slowRows` is published in the same payload and bucketed by the panel through
     the same _sortRow — and bad/mine/unk were computed from `rows` alone. Nothing in slowRows was
     counted by ANY of the three figures, so `needsYou` could drift too, not only `unknown`.

MEASURED on his Mac the same hour: rows 61 = ok 45 + missing 11 + unknown 5; the eagle said
10 / 1 / 5; and reproducing the client bucketing by hand gave exactly 10 / 1 / 5 — because that
board has no 'unmeasured' rows and its single SLOW check reads 'ok'. `len(SLOW)` is 1, so slowRows
accounts for ONE of the two; the other is an 'unmeasured' row inside `rows`.

⚠ FIXED AT THE NOUN, NOT BY FORCING EQUALITY. Setting a counter to its list's length would re-hide
exactly what the clause exposed. The standing ruling in
test_a_lane_count_names_the_population_it_counted is that the number was never wrong, only the
population it named — so the FIGURES widened to the drawn population and the panel is untouched.
[[label-outlived-referent]] [[zero-needs-a-denominator]]
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

APP = os.path.join(ROOT, "tv", "control_app.py")
UI = os.path.join(ROOT, "tv", "control_ui.html")


class TestTheEagleCountsWhatThePanelDraws(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = io.open(APP, encoding="utf-8").read()
        cls.ui = io.open(UI, encoding="utf-8").read()
        # ⚠ COMMENTS STRIPPED FOR ANY COUNT. The first cut of test_slow_surface_is_read_once
        # counted "slow_surface" in the RAW file and got 2 — one of which was the explanatory
        # comment four lines above the call. A law that counts a word in its own prose is not
        # measuring the code. Third time this shape has appeared in one session.
        # [[presence-law-vs-reachability-law]]
        from frame_authority import _executable_only
        cls.app_code = _executable_only(cls.app, APP)

    def test_both_spellings_of_not_measured_are_counted(self):
        self.assertIn('unk = [r for r in _drawn if r.get("state") in ("unknown", "unmeasured")]',
                      self.app,
                      "the server counts one spelling while the panel buckets two, so every "
                      "UNMEASURED row is drawn and not counted")

    def test_the_slow_rows_are_counted_not_only_published(self):
        self.assertIn("_drawn = list(rows) + list(_slow_rows)", self.app,
                      "slowRows is published and bucketed by the panel but counted by none of the "
                      "three figures — an unjoined end inside one payload")
        self.assertIn("_missing = [r for r in _drawn", self.app,
                      "needsYou/mine still count `rows` alone, so a missing slow row is drawn and "
                      "uncounted exactly like the unknown ones were")

    def test_slow_surface_is_read_once_and_reused(self):
        """It is a cached read, but calling it twice invites the two calls to disagree."""
        self.assertIn('"slowRows": _slow_rows,', self.app,
                      "the payload re-calls slow_surface() instead of publishing the very list "
                      "the figures were computed from — two reads, one claim")
        # ONE call, counted in EXECUTABLE source. Raw source says 2 because the comment above
        # the call names it too — see setUpClass.
        self.assertEqual(self.app_code.count("slow_surface"), 1,
                         "slow_surface should be fetched in exactly ONE place; a second call is "
                         "a second read that can disagree with the figures already computed")

    def test_the_panel_still_buckets_both_spellings_and_both_lists(self):
        """The fix must NOT have been made by narrowing the panel — that would 'agree' by
        drawing less, which is the same silence in a new place."""
        self.assertIn("r.state === 'unknown' || r.state === 'unmeasured'", self.ui,
                      "the panel stopped drawing one of the two states; agreement bought by "
                      "drawing less is not agreement")
        self.assertIn("(e.slowRows || []).forEach(_sortRow)", self.ui,
                      "the panel stopped bucketing slowRows — same objection")


# ══ THE EXECUTABLE RED-PROOF ═════════════════════════════════════════════════════════════════
RED_PROOF = [
    {
        "why": "counting one spelling again leaves every UNMEASURED row drawn and uncounted",
        "file": "tv/control_app.py",
        "find": '    unk = [r for r in _drawn if r.get("state") in ("unknown", "unmeasured")]',
        "replace": '    unk = [r for r in _drawn if r.get("state") == "unknown"]',
        "matches": 1,
    },
    {
        "why": "dropping slowRows from the counted set restores the uncounted published list",
        "file": "tv/control_app.py",
        "find": "    _drawn = list(rows) + list(_slow_rows)",
        "replace": "    _drawn = list(rows)",
        "matches": 1,
    },
    {
        "why": "narrowing the PANEL would buy agreement by drawing less, which hides it again",
        "file": "tv/control_ui.html",
        "find": "      else if (r && (r.state === 'unknown' || r.state === 'unmeasured')) unkRows.push(h);",
        "replace": "      else if (r && r.state === 'unknown') unkRows.push(h);",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
