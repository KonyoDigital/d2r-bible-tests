# -*- coding: utf-8 -*-
"""v3290 — THE SHELF MUST ACCOUNT FOR EVERY RUN IT DOES NOT DRAW.

Konyo, 2026-09-18: *"the shelf is showing 12 runs why not 8? what happened there? make sure its a
unified logic and the console knows FIFO on the 8 only so nothing is mismatched and not synced"*,
and at the river strip: *"THE RIVER also reading some weird not synced numbers here should either
be hidden or fixed and synced accordingly"*.

MEASURED on his console, 2026-09-18 — five surfaces, five numbers, each correct for a DIFFERENT
question:

    /api/sessions   419 runs
    /api/river       63 reels, 11 on the shelf, 454 closed out
    the pipeline     11 reels surveyed
    ACTIVITY         15 runs — over a 14-DAY WINDOW
    FIFO              8
    the SHELF        12 cards

⚠⚠ **THEY MUST NOT BE FORCED EQUAL, AND THAT IS A STANDING RULING, NOT A PREFERENCE.**
`test_a_lane_count_names_the_population_it_counted` (2026-09-13) measured this exact shape and
concluded: *"THE NUMBER WAS NEVER WRONG... Only the NOUN was wrong. This file guards the noun"*,
and *"THE STRIP IS NOT THE DEFECT — DO NOT FIX IT. Its arithmetic is internally consistent...
A second attempt there would undo work that is correct."* So this guards the noun on the surface
he named, and leaves the river alone.

**What was actually broken was a silent subtraction.** Fixtures, retired and unknown each had a
chip; a STUB — a run with under three real rows and no reel, which never HAD film — was dropped
with no counter anywhere. MEASURED: **154 of his 419 runs**. The shelf drew 12 cards and said
nothing about the other 407.

With the stub bucket counted, the population closes exactly:

    12 shown + 8 fixtures + 232 retired + 154 stubs + 13 unknown = 419

⚠ And it refuses to hide a remainder: if those parts ever stop summing to the run total, the
difference is PRINTED rather than absorbed. An unexplained gap is precisely what made him ask.
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

from frame_authority import _executable_only  # noqa: E402

UI = os.path.join(ROOT, "tv", "control_ui.html")


class TestTheShelfAccountsForEveryRun(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code = _executable_only(io.open(UI, encoding="utf-8").read(), ".js")

    def test_a_stub_is_counted_rather_than_dropped(self):
        """The silent subtraction: 154 of his 419 runs left by this branch uncounted."""
        self.assertIn("if (!_shBuildGhosts && sm && sm.stub) { _shStubN++; return ''; }", self.code,
                      "a stub is dropped without being counted, so the shelf shows 12 cards and "
                      "says nothing about where the other runs went")
        self.assertIn("var _shRetiredN = 0, _shUnknownN = 0, _shStubN = 0;", self.code,
                      "the stub counter is not declared beside its siblings")

    def test_the_head_says_how_many_of_how_many(self):
        self.assertIn("_shShownN + ' of ' + _shRunsN + ' runs kept film'", self.code,
                      "the head names no denominator, so '12' answers a question nobody can see")
        self.assertIn("var _shShownN = cards.filter(", self.code,
                      "the shown count must be measured BEFORE join('') - afterwards the "
                      "population is unknowable")

    def test_an_unexplained_remainder_is_printed_not_absorbed(self):
        """The guard that keeps the line honest when a NEW dropped bucket appears."""
        self.assertIn("var _named = _shShownN + _shFixtureN + _shStubN + _shRetiredN + _shUnknownN;",
                      self.code, "nothing compares the named buckets against the run total")
        self.assertIn("unaccounted for", self.code,
                      "a remainder is absorbed silently, which is the exact defect this replaces")

    def test_the_stub_bucket_has_a_chip_like_its_three_siblings(self):
        self.assertIn("sh-chip-stub", self.code,
                      "a counted bucket with no chip is still invisible to him")


# ══ THE EXECUTABLE RED-PROOF ═════════════════════════════════════════════════════════════════
RED_PROOF = [
    {
        "why": "un-counting the stubs restores a silent 154-run subtraction",
        "file": "tv/control_ui.html",
        "find": "      if (!_shBuildGhosts && sm && sm.stub) { _shStubN++; return ''; }",
        "replace": "      if (!_shBuildGhosts && sm && sm.stub) { return ''; }",
        "matches": 1,
    },
    {
        "why": "dropping the denominator leaves 12 answering an invisible question",
        "file": "tv/control_ui.html",
        "find": "              _shShownN + ' of ' + _shRunsN + ' runs kept film'",
        "replace": "              'your reels'",
        "matches": 1,
    },
    {
        "why": "absorbing the remainder is how the gap became invisible in the first place",
        "file": "tv/control_ui.html",
        "find": "                return _rest > 0 ? ' \\u00b7 \\u26a0 ' + _rest + ' unaccounted for' : '';",
        "replace": "                return '';",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
