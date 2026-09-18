# -*- coding: utf-8 -*-
"""v3311 (#31) — THE SHADOW IS PAID FOR HIS TESTIMONY, AND FED WHAT LIVE IS FED.

Two corrections to the shadow gate. Neither arms anything and neither changes a live verdict —
`confluence()` has exactly ONE caller (`wilson_shadow`) and the tier's own note says the weighting
"only reports". That was checked BEFORE either was touched. [[regression-guard]]

⚠ HIS RULING ON THE THIRD PIECE IS THE OPPOSITE OF BUILDING IT, and it is recorded here so nobody
reverses it by accident: "leave it off and surgically remove it we need pruning" (2026-09-18).
The Wilson lock must NOT be wired to the prune. This law is about the two CORRECTIONS only.

── 1. HIS MANUAL TICK WAS PAID 0.00 ────────────────────────────────────────────────────────────
WITNESS_TIER was written before three tags existed. `hand` (v2462), `cross-surface` (v2380) and
`same-slot` (v2393) were all added to witnesses() afterwards, and confluence() scores an unknown
tag 0.0. So the LIVE gate counted his manual tick as a full witness while the SHADOW paid it
NOTHING — against his own standing ruling, 2026-09-02: *"manual anything is enough witness
obivously"*. A STALE LAW, not a stale reading. [[manual-tally-is-witness]]

EVERY WEIGHT IS DERIVED, NOT PICKED:
  hand          1.00  CONFLUENCE_FLOOR is 1.00, so "enough witness on its own" HAS a number.
                      ⚠ It keeps its OWN TAG: this file insists `hand` must never masquerade as
                      cross-reel or printed, because a reader asking WHY a name grounded must see
                      "he says so". Equal weight, separate name — the requirement is identity.
  cross-surface 0.70  his own words for the case: "thats two witnesses". Two independent views of
                      one item — the same class as cross-lane, priced with it.
  same-slot     0.30  "A WITNESS, NOT A NAME" — it corroborates what another signal proposed and
                      must never ground alone, so it is priced with cross-frame, the weakest tier.

── 2. THE SHADOW WAS SHOWN A POORER WITNESS LIST THAN LIVE, INSIDE ONE CALL ─────────────────────
`_gate_verdict_live` received `surface_of=surface_of`; `wilson_shadow` did not, and had no such
parameter at all. So a name grounded via CROSS-SURFACE was invisible to the shadow, the two rules
were compared on DIFFERENT INPUTS, and every resulting difference was filed as a disagreement
about POLICY when it was a difference in what each was allowed to SEE.

MEASURED, same sightings, resolver the only variable:
    without -> tags ['cross-frame'],                  confluence 0.30, wouldPass False
    with    -> tags ['cross-frame', 'cross-surface'], confluence 1.00, wouldPass True
A comparison whose two sides are fed differently measures the feeding.
[[the-unjoined-end]] [[feedback-suspect-the-instrument]]
"""
import io
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import chronicle_retro as cr                             # noqa: E402


class TestTheShadowIsFedWhatLiveIsFed(unittest.TestCase):

    # ── 1. the tier ──────────────────────────────────────────────────────────────────────────
    def test_his_manual_tick_is_worth_something(self):
        """⚠ THE ONE THAT CONTRADICTED HIS OWN RULING."""
        w = cr.confluence(["hand"])
        self.assertGreater(
            w, 0.0,
            "the shadow pays his manual tick %.2f. The LIVE gate counts it as a full witness, so "
            "every name he ticked by hand arrives at the comparison as evidence on one side and "
            "nothing on the other — and his ruling is 'manual anything is enough witness "
            "obivously'." % w)
        self.assertGreaterEqual(
            w, cr.CONFLUENCE_FLOOR,
            "his tick is weighed at %.2f against a confluence floor of %.2f, so it cannot ground "
            "a name ALONE. 'Enough witness' has a number in this file and that number is the "
            "floor." % (w, cr.CONFLUENCE_FLOOR))

    def test_every_tag_witnesses_can_emit_has_a_weight(self):
        """STRUCTURAL: the defect was a tag added after the table, and it will happen again."""
        emitted = {"printed", "hand", "cross-surface", "same-slot",
                   "cross-lane", "cross-reel", "cross-reel-3+", "cross-frame"}
        unweighed = sorted(t for t in emitted if cr.confluence([t]) <= 0.0)
        self.assertEqual(
            unweighed, [],
            "%d tag(s) that witnesses() can emit score ZERO in the tier: %s. An unknown tag is "
            "scored 0.0 by confluence(), so a tag added after this table silently stops counting "
            "— which is exactly how `hand`, `cross-surface` and `same-slot` came to be worth "
            "nothing for versions." % (len(unweighed), unweighed))

    def test_a_corroborating_tag_still_cannot_ground_alone(self):
        """⚠ THE OTHER DIRECTION. Fixing a zero must not turn a witness into a name."""
        self.assertLess(
            cr.confluence(["same-slot"]), cr.CONFLUENCE_FLOOR,
            "`same-slot` alone now clears the confluence floor, so agreeing on a CELL could ground "
            "a name nothing else proposed. slot_identity's own words: it is A WITNESS, NOT A NAME "
            "— it corroborates something another signal proposed.")
        self.assertLess(
            cr.confluence(["cross-frame"]), cr.CONFLUENCE_FLOOR,
            "`cross-frame` alone grounds; two frames inside ONE reel is the weakest evidence there "
            "is and must never be sufficient by itself.")

    # ── 2. the input asymmetry ───────────────────────────────────────────────────────────────
    def test_the_shadow_sees_the_same_surfaces_live_sees(self):
        """BEHAVIOURAL, and the resolver is the ONLY variable between the two runs."""
        sights = [{"reel": "reel_a", "frame": "f1", "conf": 0.9},
                  {"reel": "reel_a", "frame": "f2", "conf": 0.9}]
        surf = {"f1": "stash", "f2": "inventory"}

        blind = cr.wilson_shadow(sights)
        seeing = cr.wilson_shadow(sights, surface_of=lambda sg: surf.get(sg.get("frame")))

        self.assertNotIn(
            "cross-surface", blind["tags"],
            "the fixture is wrong: without a resolver there is no way to know two surfaces were "
            "involved, so this case cannot show the difference it exists to show.")
        self.assertIn(
            "cross-surface", seeing["tags"],
            "wilson_shadow was handed a surface resolver and still did not see cross-surface, so "
            "the parameter is accepted and dropped — the shadow keeps judging a name on a poorer "
            "witness list than live used, and every difference is filed as a policy disagreement.")

    def test_the_caller_actually_hands_it_over(self):
        """A parameter nothing passes is the unjoined end this correction is about."""
        with io.open(os.path.join(HERE, "chronicle_retro.py"), encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn(
            "wilson_shadow(sightings, conf_floor, min_witnesses, surface_of=surface_of)", src,
            "gate_verdict still calls wilson_shadow WITHOUT surface_of while handing it to "
            "_gate_verdict_live one line above. The signature would accept it and no caller would "
            "ever pass it. [[the-unjoined-end]]")


if __name__ == "__main__":
    unittest.main(verbosity=2)


RED_PROOF = [
    {
        "why": "dropping hand from the tier pays his manual tick 0.00 again, against his own ruling",
        "file": "tv/chronicle_retro.py",
        "find": '    "hand":          1.00,',
        "replace": '    "_hand_removed": 1.00,',
        "matches": 1,
    },
    {
        "why": "pricing same-slot at the floor lets a CELL agreement ground a name nothing proposed",
        "file": "tv/chronicle_retro.py",
        "find": '    "same-slot":     0.30,',
        "replace": '    "same-slot":     1.00,',
        "matches": 1,
    },
    {
        "why": "taking the resolver back shows the shadow a poorer witness list than live saw",
        "file": "tv/chronicle_retro.py",
        "find": "    tags = witnesses(sightings, surface_of=surface_of)",
        "replace": "    tags = witnesses(sightings)",
        "matches": 1,
    },
    {
        "why": "a caller that stops passing the resolver makes the parameter decorative",
        "file": "tv/chronicle_retro.py",
        "find": "        sh = wilson_shadow(sightings, conf_floor, min_witnesses, surface_of=surface_of)",
        "replace": "        sh = wilson_shadow(sightings, conf_floor, min_witnesses)",
        "matches": 1,
    },
]
