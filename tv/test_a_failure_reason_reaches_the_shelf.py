# -*- coding: utf-8 -*-
"""v3400 — the reason retention FAILED must reach the shelf, and a new machine is not a broken one.

⚠⚠ THE DEFECT THIS PINS, MEASURED TWICE. `reel_retention.plan()` publishes its failure reason
under `why`. `shelf_driver.work()` read `p.get("say")` — a key that exists only on the SUCCESS
payload — so on EVERY failure it fell through to the generic string "retention could not read this
shelf". v3393 had already taught plan() to answer "no footage tree on this machine yet", and its
own comment names the shelf as a consumer that "drew a 0x0 box". The shelf never received a word
of it: two halves, each correct, never joined. [[the-unjoined-end]]

MEASURED on his ALT console 2026-09-20 (v3395): its eagle read "the shelf driver's last beat 2.5h
ago reported NOT ok: retention could not read this shelf" on a machine whose only fault is that
nothing has ever been recorded on it. Reproduced on the Mac against an absent tree.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

# ⚠ THIS FILE PRINTS ITS FINDINGS AND THEY CARRY NON-ASCII. On a cp1255 console that crashes
# WHILE REPORTING, so a clean tree would exit non-zero for a reason unrelated to the check.
# The pre-push gate refused a sibling gate for exactly this hours ago.
from console_safe import enable as _console_safe_enable  # noqa: E402
_console_safe_enable()

import console_doctor as cd  # noqa: E402
import reel_retention as rr  # noqa: E402
import shelf_driver as sd  # noqa: E402

GENERIC = "retention could not read this shelf"

RED_PROOF = [
    {
        "why": "reading only `say` throws plan's reason away again - the shelf falls back to the "
               "generic string and a never-filmed machine reports itself broken",
        "file": "tv/shelf_driver.py",
        "find": '                "why": str(p.get("say") or p.get("why")\n                           or "retention could not read this shelf"),',
        "replace": '                "why": str(p.get("say") or "retention could not read this shelf"),',
        "matches": 1,
    },
    {
        "why": "without the machine-readable flag the heart can only grep English, so a console "
               "that has simply never filmed is reported as a stalled lane",
        "file": "tv/reel_retention.py",
        "find": '            return {"ok": False, "candidates": [], "kept": [], "neverRecorded": True,',
        "replace": '            return {"ok": False, "candidates": [], "kept": [],',
        "matches": 1,
    },
]

ABSENT = os.path.join(HERE, "__no_such_footage_tree_v3400__", "hist")


class TestAFailureReasonReachesTheShelf(unittest.TestCase):

    def test_BASELINE_plan_refuses_an_absent_tree_with_a_reason(self):
        """If this stops holding, every case below is measuring nothing."""
        p = rr.plan(ABSENT)
        self.assertFalse(p.get("ok"), "an absent footage tree must not plan successfully")
        self.assertTrue(str(p.get("why") or "").strip(),
                        "plan() refused without saying why - there is no reason to carry")

    def test_plan_marks_a_never_recorded_machine_as_a_FLAG_not_only_prose(self):
        p = rr.plan(ABSENT)
        self.assertIs(p.get("neverRecorded"), True,
                      "a consumer can only tell a new machine from a broken one by grepping "
                      "English, which breaks the moment the wording improves")

    def test_the_shelf_PUBLISHES_plans_reason_and_not_the_generic_fallback(self):
        """THE JOIN. This is the whole defect."""
        w = sd.work(ABSENT)
        self.assertFalse(w.get("ok"))
        why = str(w.get("why") or "")
        self.assertNotEqual(why, GENERIC,
                            "the shelf published the generic fallback while plan() had a real "
                            "reason - the reason was thrown away by reading the wrong key")
        self.assertIn("no footage tree", why,
                      "the shelf did not publish plan's own sentence, it published %r" % why[:70])

    def test_the_shelf_carries_the_flag_through(self):
        self.assertIs(sd.work(ABSENT).get("neverRecorded"), True)

    def test_the_beat_carries_it_to_whoever_supervises(self):
        b = sd.beat(ABSENT, write=False)
        self.assertIs(b.get("neverRecorded"), True,
                      "the beat dropped the flag, so the heart cannot tell a new console from a "
                      "stalled lane no matter what work() knew")
        self.assertIn("no footage tree", str(b.get("why") or ""))

    def test_a_reason_plan_DOES_give_is_never_overwritten(self):
        """A failure that is NOT the never-filmed case must still reach the surface verbatim."""
        real = sd.plan
        try:
            sd.plan = lambda h=None: {"ok": False, "why": "the disk went away mid-read",
                                      "neverRecorded": False}
            w = sd.work("anything")
            self.assertEqual(w.get("why"), "the disk went away mid-read")
            self.assertIs(w.get("neverRecorded"), False)
        finally:
            sd.plan = real

    def test_the_generic_fallback_fires_ONLY_when_plan_gives_no_reason_at_all(self):
        real = sd.plan
        try:
            sd.plan = lambda h=None: {"ok": False}
            self.assertEqual(sd.work("anything").get("why"), GENERIC,
                             "with nothing to say, the fallback is the honest answer")
        finally:
            sd.plan = real

    def test_the_heart_calls_a_never_filmed_console_UNMEASURED_not_MISSING(self):
        """#138's ruling, reaching the shelf. A new console is not a broken lane."""
        real = sd.last_beat
        try:
            sd.last_beat = lambda: {"at": cd.time.time() * 1000.0, "ok": False,
                                    "neverRecorded": True,
                                    "why": "no footage tree on this machine yet"}
            state, why = cd._check_the_shelf_lanes_are_still_reading()
            self.assertEqual(state, cd.UNMEASURED,
                             "a console that has never filmed was reported as %s - a red row he "
                             "did not cause and cannot act on: %s" % (state, why[:80]))
            # ⚠ ASSERT THE CLAIM, NOT A FRAGMENT. The first cut looked for "never" and the
            # sentence says "nothing has EVER been recorded" - correct English, failing
            # test. Anchor on the half that carries the distinction instead.
            self.assertIn("not a lane that stopped", why)
        finally:
            sd.last_beat = real

    def test_a_console_that_HAS_filmed_and_then_failed_is_still_MISSING(self):
        """⚠ THE MIRROR. The new branch must not swallow a genuine stalled lane."""
        real = sd.last_beat
        try:
            sd.last_beat = lambda: {"at": cd.time.time() * 1000.0, "ok": False,
                                    "neverRecorded": False,
                                    "why": "the disk went away mid-read"}
            state, why = cd._check_the_shelf_lanes_are_still_reading()
            self.assertEqual(state, cd.MISSING,
                             "a real retention failure was downgraded to %s - the new branch "
                             "swallowed the case the row exists for" % state)
        finally:
            sd.last_beat = real


if __name__ == "__main__":
    unittest.main(verbosity=2)
