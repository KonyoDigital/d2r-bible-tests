# -*- coding: utf-8 -*-
"""v2984 — THE ARMED PRUNE MAY NEVER REACH A REEL, AND THE FLOOR MUST STAND.

HIS INSTRUCTION, 2026-09-12: "arm it", said twice. `_PRUNE_SAFE_TO_RUN` is now True. These are the
two facts that make that safe, and they are LOAD-BEARING rather than incidental — so they are
pinned here instead of being trusted.

⚠⚠ THE ARGUMENT AGAINST ARMING WAS ABOUT THE WRONG POPULATION. Task #78 said "the moment the prune
is armed this becomes 798 frames of his own footage deleted from reels retention wanted held".
That is FALSE, and measuring it is what unblocked his instruction. There are two engines and they
never touch the same file:

    prune_reclaimable() -> frame_authority.plan_frames()          REPORTS. Deletes nothing, ever.
    _prune_once()       -> sig_diff + stash_panel_verdict + os.remove    THE ACTUAL DELETER.

Measured on his tree the moment before arming:
    loose frames _prune_once can see        23     (_PRUNE_FLOOR is 200, so the pass refuses)
    plan_frames prunable                   798     all 798 INSIDE a reel_* subdirectory
    OVERLAP                                  0
_prune_once globs `HIST_DIR/f_*.jpg`, and rule 1 of its own charter is "never touch a REEL
directory". The 798 is a plan with no actor — nothing in the tree executes it.
[[plumbing-with-no-tap]] [[label-outlived-referent]]

⚠ v2187 IS SUPERSEDED AND I NEARLY REPEATED IT AS FACT. Its "Do not arm" rests on the deletable
class being the TEXT-BEARING one, and on the OCR-liveness proof being absent from the tree. v2197
landed that proof. Read at the decision site (control_app.py:18800-18836): text present + no panel
-> KEEP, gate broke -> KEEP, and only the SILENT/blank class is deletable, and only where LaneCanary
proves the lane was live around that frame. Caught by running the deleter for real and reading its
own sentence: "119 blank frame(s) freed (the OCR lane passed 2 of 2 deliberate probe(s)), 0 kept for
want of that proof." [[inherited-claim-is-not-evidence]]

⚠ TEST 1 IS THE REAL ONE AND IT RUNS THE DELETER FOR REAL. Not dry_run, not a source read — a temp
HIST_DIR with more loose frames than the floor so the pass genuinely executes, plus a reel_*
subdirectory of frames that must all still be on disk afterwards.
"""
import io
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import control_app as CA  # noqa: E402


def _jpg(path, shade):
    from PIL import Image
    Image.new("RGB", (64, 48), (shade, shade, shade)).save(path, "JPEG", quality=60)


class TheArmedPruneCannotReachAReel(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp(prefix="prune_reach_")
        self.addCleanup(shutil.rmtree, self.d, True)

    def test_a_real_pass_never_removes_a_frame_inside_a_reel(self):
        old = time.time() - (CA._PRUNE_GRACE_S * 4)
        # more loose frames than the floor, so the pass actually runs rather than refusing
        for i in range(CA._PRUNE_FLOOR + 25):
            q = os.path.join(self.d, "f_%d.jpg" % (1700000000000 + i))
            _jpg(q, 120)
            os.utime(q, (old, old))
        # ⚠⚠ THE REEL NEEDS ITS OWN ABOVE-FLOOR POPULATION, AND THIS TEST WAS BLIND WITHOUT IT.
        # First drill: the tamper repoints the glob at `root/*/f_*.jpg`, which sees ONLY the reel —
        # and with 6 frames there, `len(live) < floor` refused the pass, so nothing was deleted and
        # the law passed through its own defeat. The FLOOR was masking the containment break. With
        # more than the floor inside the reel too, neither glob can hide behind it: the honest code
        # still deletes only loose frames, the tampered code reaches the reel and this goes red.
        # [[feedback-blind-fixture-green-gate]] [[sabotage-is-usually-the-wrong-one]]
        reel = os.path.join(self.d, "reel_s_1_2")
        os.makedirs(reel)
        sealed = []
        for i in range(CA._PRUNE_FLOOR + 25):
            q = os.path.join(reel, "f_%d.jpg" % (1600000000000 + i))
            _jpg(q, 120)                      # deliberately IDENTICAL to the loose ones
            os.utime(q, (old, old))
            sealed.append(q)

        dropped, freed, why = CA._prune_once(hist_dir=self.d)

        alive = [q for q in sealed if os.path.exists(q)]
        self.assertEqual(
            len(alive), len(sealed),
            "the armed prune deleted %d frame(s) from INSIDE a reel directory — its own charter's "
            "rule 1 is 'never touch a REEL directory', and these are his sealed evidence. "
            "(dropped=%s freed=%s why=%r)" % (len(sealed) - len(alive), dropped, freed, why))

    def test_the_floor_still_refuses_a_small_pass(self):
        old = time.time() - (CA._PRUNE_GRACE_S * 4)
        for i in range(5):
            q = os.path.join(self.d, "f_%d.jpg" % (1700000000000 + i))
            _jpg(q, 90)
            os.utime(q, (old, old))
        dropped, freed, why = CA._prune_once(hist_dir=self.d)
        self.assertEqual((dropped, freed), (0, 0),
                         "the pass deleted below the floor: %r" % (why,))
        self.assertIn("floor", (why or "").lower(),
                      "the refusal must SAY it was the floor, or 'nothing to free' and 'refused' "
                      "look identical on his console: %r" % (why,))

    def test_the_floor_is_not_lowered_to_nothing(self):
        self.assertGreaterEqual(
            CA._PRUNE_FLOOR, 200,
            "the floor is the second of the two facts that make arming safe; lowering it puts the "
            "v2187 tooltip case back in reach on an ordinary session")

    def test_the_switch_is_armed_and_the_reason_is_recorded(self):
        src = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        self.assertTrue(CA._PRUNE_SAFE_TO_RUN, "the prune is disarmed; he asked for it armed")
        self.assertIn("THE TWO DELETERS ARE DISJOINT", src,
                      "the measurement that justified arming is gone — without it the next reader "
                      "sees only v2187's 'Do not' and either re-disarms it blindly or, worse, "
                      "trusts the arming without knowing what made it safe")


import time  # noqa: E402  (used by the fixtures above)

RED_PROOF = [
    {
        "why": "letting the glob reach into subdirectories is the containment violation itself: "
               "the deleter would start eating frames inside his sealed reels",
        "file": "control_app.py",
        "find": 'live = [q for q in _g.glob(os.path.join(root, "f_*.jpg"))',
        "replace": 'live = [q for q in _g.glob(os.path.join(root, "*", "f_*.jpg"))',
        "matches": 1,
    },
    {
        "why": "dropping the floor to zero puts the v2187 tooltip class in reach on any session",
        "file": "control_app.py",
        "find": "_PRUNE_FLOOR = 200",
        "replace": "_PRUNE_FLOOR = 0",
        "matches": 1,
    },
    {
        "why": "deleting the disjointness measurement leaves the arming unexplained",
        "file": "control_app.py",
        "find": "THE TWO DELETERS ARE DISJOINT",
        "replace": "_HEART2_TAMPERED_",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
