# -*- coding: utf-8 -*-
"""v2720 — HIS RULING, JOINED, AND THE CONDITION ENFORCED RATHER THAN ASSUMED.

Konyo, 2026-09-06, answering the question `control_app._seal_extracted` itself flagged as
not-mine-to-decide (*"it is the rule that governs deleting his recordings"*):

    "as long as its ledgered and extracted properly and tallied where needed.. it can continue
     down the river to tombstone i dont see why not..? and delete.."

A CONDITIONAL YES, AND THE CONDITION IS THE ENTIRE JOB.

=== WHAT WAS ALREADY BUILT, AND WHAT WAS NEVER JOINED ===
`seal_verdict()` has answered COVERED / EMPTY / UNEVIDENCED since v2702, written precisely so
"examined and there was genuinely nothing here" would stop being scored identically to "nobody
looked". It was correct, and it was called by ONE place, for a REPORT. Both functions that
actually DECIDE still asked the old binary `seal_covers_extraction()`:

    reel_river.py:164        the FRAME DOOR
    frame_authority.py:323   frame_verdict — "may this frame be deleted?"

So the collapse the good vocabulary existed to end was still happening at every site that
mattered. That is [[the-unjoined-end]], and it is why he asked for it to be connected to the heart:
unconnected, it was a lucky find; connected, it is a visible state. [[join-gate-heart]]

=== ⚠⚠ AND THE OBVIOUS JOIN WAS TOO GENEROUS — MEASURED BEFORE SHIPPING ===
`seal_verdict` scores a seal EMPTY when `examinedEmpty` is set OR when `extractedWhy` merely
contains the word "nothing". Across his 31 real seals:

    23 scored EMPTY
       17 carry `examinedEmpty: True`
        6 qualify ONLY on the string, and their why is literally "nothing was taken"

"nothing was taken" is the DEFAULT branch of `_seal_extracted` for any sweep that grounded no rows.
It says the sweep found nothing. It does NOT say anyone established there was nothing to find, and
his ruling was explicitly conditional on the examination being real. Wiring `!= UNEVIDENCED`
straight into the deleter would have released 6 reels on a string match.

So the DECIDERS ask `seal_releases_frames()` — COVERED, or EMPTY *with `examinedEmpty` declared* —
while reporting keeps the looser `seal_verdict`, where a measured-zero SHOULD stay visible.
Measured after: 17 release, 14 hold. [[unknown-stays-unknown]] [[manual-tally-is-witness]]

⚠ SAFETY: this changes what is ELIGIBLE, never what is deleted. The prune stays behind
`_PRUNE_SAFE_TO_RUN = False` and `retention_may_act()`, both still his.
"""
import io
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

import frame_authority as FA


def _code(path):
    """-> source with comments stripped, so PROSE cannot satisfy a CODE check.

    This file's own docstring names `seal_covers_extraction` while forbidding the deciders from
    calling it. [[source-reading-guard]]
    """
    s = io.open(os.path.join(HERE, path), encoding="utf-8").read()
    s = re.sub(r'"""(?:.|\n)*?"""', " ", s)
    return re.sub(r"(?m)#.*$", " ", s)


class ExaminedEmptyReleases(unittest.TestCase):

    # ── the CONDITION: his ruling was conditional, so the condition is the law ────────────────
    def test_a_seal_claiming_nothing_was_taken_does_NOT_release(self):
        """The over-permission this gate exists to prevent. 6 of his 31 seals look like this."""
        ok, why = FA.seal_releases_frames(
            {"extracted": [], "extractedWhy": "nothing was taken", "rows": 0})
        self.assertFalse(
            ok, "a seal saying only 'nothing was taken' released its frames. That is the DEFAULT "
                "for any sweep that grounded no rows — it says the sweep found nothing, not that "
                "anyone established there was nothing to find. His yes was conditional."
        )
        self.assertIn("examinedEmpty", why, "the refusal must name what is missing")

    def test_a_DECLARED_examined_empty_seal_DOES_release(self):
        """The other direction — otherwise the ruling was never implemented at all."""
        ok, _ = FA.seal_releases_frames(
            {"extracted": [], "extractedWhy": "examined and there was nothing to take",
             "examinedEmpty": True, "rows": 0})
        self.assertTrue(ok, "a seal that DECLARED examinedEmpty was still held — his ruling says "
                            "it may continue down the river")

    def test_a_seal_that_never_looked_still_HOLDS(self):
        """UNEVIDENCED is untouched. Nobody-looked is not measured-empty."""
        for row in ({}, {"promptVer": "p1"}, {"extracted": None}):
            ok, _ = FA.seal_releases_frames(row)
            self.assertFalse(ok, "a seal with no evidence released frames: %r" % (row,))

    def test_a_COVERED_seal_still_releases(self):
        ok, _ = FA.seal_releases_frames(
            {"extracted": list(FA.EXTRACTION_CONTRACT), "rows": 3})
        self.assertTrue(ok, "a seal that took the full contract was held")

    def test_examinedEmpty_must_be_TRUE_not_merely_present(self):
        """A falsy flag is not a declaration. `examinedEmpty: False` is the sweep saying NO."""
        # ⚠⚠ THIS LAW WAS VACUOUS ON ITS FIRST CUT AND THE SABOTAGE PASS CAUGHT IT. The rows below
        # originally omitted `rows: 0`, and `seal_verdict` requires that before it will say EMPTY —
        # so EVERY case returned False for a reason that had nothing to do with examinedEmpty, and
        # a sabotage changing `is True` to `is not None` stayed GREEN. Proven by measurement:
        # with the key absent, even examinedEmpty=True refused to release.
        # A law whose cases all fail for an unrelated reason tests nothing.
        # [[sabotage-is-usually-the-wrong-one]] [[zero-needs-a-denominator]]
        base = {"extracted": [], "extractedWhy": "nothing was taken", "rows": 0}
        ok, _ = FA.seal_releases_frames(dict(base, examinedEmpty=True))
        self.assertTrue(ok, "the CONTROL for this law does not hold: a declared examinedEmpty seal "
                            "must release, or every case below fails for the wrong reason")
        for val in (False, None, 0, "", "no"):
            ok, _ = FA.seal_releases_frames(dict(base, examinedEmpty=val))
            self.assertFalse(ok, "examinedEmpty=%r released frames — only True is a declaration" % (val,))

    # ── the JOIN: the deciders must not fall back to the binary question ──────────────────────
    def test_the_DELETION_GATE_asks_the_strict_question(self):
        """⚠ The whole point. seal_verdict existed and correct for 18 versions while every
        DECIDER asked the old binary question. [[the-unjoined-end]]"""
        src = _code("frame_authority.py")
        m = re.search(r"def frame_verdict\((?:.|\n)*?\n(?=def )", src)
        self.assertIsNotNone(m, "frame_verdict is not where this gate expects it")
        body = m.group(0)
        self.assertIn("seal_releases_frames", body,
                      "the DELETION GATE does not ask the strict question — it can no longer tell "
                      "'examined and empty' from 'nobody looked', which is what it is for")
        self.assertNotIn("seal_covers_extraction(", body,
                         "the deletion gate CALLS the binary question again")

    def test_the_FRAME_DOOR_asks_the_strict_question(self):
        src = _code("reel_river.py")
        self.assertIn("seal_releases_frames", src,
                      "reel_river's frame door does not ask the strict question")
        # ⚠ GRADE THE CALL, NOT THE MENTION. The first cut asserted the string was absent from
        # the whole file and failed on `FRAME_QUESTION`, a LABEL naming the decider. That was a
        # real find — the label had outlived its referent and now named the wrong function, so it
        # was repointed — but the assertion itself was too broad and would fail on any comment.
        # [[source-reading-guard]] [[label-outlived-referent]]
        self.assertNotIn("seal_covers_extraction(", src,
                         "the frame door CALLS the binary question again")

    def test_REPORTERS_may_still_use_the_looser_verdict(self):
        """⚠ ANTI-OVER-CORRECTION. A measured-zero must stay VISIBLE in a report — collapsing it
        into nobody-looked is the defect seal_verdict was written to end. Only DECIDERS tighten."""
        src = _code("extract_gap.py")
        self.assertIn("seal_verdict", src,
                      "extract_gap stopped reporting the three-answer verdict — a measured zero "
                      "would read as nobody-looked again, which is what v2702 fixed")


if __name__ == "__main__":
    unittest.main(verbosity=2)
