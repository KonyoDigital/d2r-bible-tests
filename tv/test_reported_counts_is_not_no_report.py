# -*- coding: utf-8 -*-
"""v3169 (#82) — "HAS NOT REPORTED" MUST NOT BE SAID ABOUT A MACHINE THAT REPORTED.

HIS CORRECTION, 2026-09-15. He sent the cross-reference panel reading

    "Dean has not reported which set pieces it holds yet - that is 'we have not heard from
     it', not 'it has none'. It publishes on its next heartbeat."

beside his own fleet card reading **DEAN · SETS 131/135 · UNIQUES 0/403 · RUNEWORDS 98/99**,
and said: *"dean already synced his sets something is regressed here"* and then, with a second
screenshot, *"i m saying that he has it even says it here"*.

MEASURED on his live /api/fleet at that moment - Dean's row carried
`tally.sets {have 131, total 135}` and `maskWhy {'sets': 'no board window'}`, `masks: None`.

SO THE SENTENCE WAS WRONG TWICE OVER:
  1. HE DID REPORT. The counts were on the wire. What was missing is the per-item MASK - the
     bitmask that lets the panel NAME pieces rather than count them. "has not reported" is a
     label that stopped being true of the number printed beside it. [[label-outlived-referent]]
  2. "IT PUBLISHES ON ITS NEXT HEARTBEAT" IS A PROMISE THAT CANNOT BE KEPT. The row already
     said why: no board window on that machine. It will fail identically on every heartbeat
     until one is open. A false "just wait" turns a fixable condition into an invisible one.

AND THE REASON WAS PUBLISHED BUT NEVER READ: `maskWhy` appeared ZERO times in control_ui.html.
[[the-unjoined-end]] [[zero-needs-a-denominator]]
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)


def _dean(tally=None, mask_why=None):
    r = {"machine": "LAPTOP-QNFL860M", "nickname": "Dean", "os": "windows",
         "ver": "v3156", "masks": None, "t": 1789431849.587}
    if tally is not None:
        r["tally"] = tally
    if mask_why is not None:
        r["maskWhy"] = mask_why
    return r


class ReportedCountsIsNotNoReport(unittest.TestCase):

    def setUp(self):
        import control_app
        self.c = control_app
        self._orig = control_app.fleet_presence

    def tearDown(self):
        self.c.fleet_presence = self._orig

    def _compare(self, row, ledger="sets"):
        fleet = {"online": [], "offline": [row], "stale": False}
        self.c.fleet_presence = lambda *a, **k: fleet
        return self.c.fleet_compare("LAPTOP-QNFL860M", ledger)

    # the exact state he screenshotted
    def test_a_machine_that_reported_counts_is_not_called_unreported(self):
        out = self._compare(_dean(tally={"sets": {"have": 131, "total": 135}, "ok": True},
                                  mask_why={"sets": "no board window"}))
        why = out.get("why") or ""
        self.assertNotIn("has not reported", why,
                         "he read this beside a card showing SETS 131/135 and said 'he has it, "
                         "even says it here'")
        self.assertIn("131", why, "the count he can see must appear in the sentence about it")

    def test_the_reason_the_mask_is_missing_is_named(self):
        out = self._compare(_dean(tally={"sets": {"have": 131, "total": 135}, "ok": True},
                                  mask_why={"sets": "no board window"}))
        self.assertIn("no board window", out.get("why") or "",
                      "the server published maskWhy and the panel rendered it nowhere")
        self.assertEqual(out.get("maskWhy"), "no board window",
                         "and it must be on the record as a field, not only inside prose")

    def test_it_does_not_promise_a_heartbeat_that_cannot_deliver(self):
        out = self._compare(_dean(tally={"sets": {"have": 131, "total": 135}, "ok": True},
                                  mask_why={"sets": "no board window"}))
        # ⚠ THE FIRST CUT OF THIS ASSERTION WAS BLIND, and the red-proof is what caught it.
        # It looked for "publishes on its next heartbeat" while the fallback actually says
        # "publishes THE LIST on its next heartbeat" - a substring the code cannot emit, so the
        # law could not fail. Matching on "next heartbeat" is what the claim is really about:
        # when the machine has ALREADY given a reason, no beat is going to change it.
        # [[sabotage-is-usually-the-wrong-one]] [[source-reading-guard]]
        self.assertNotIn("next heartbeat", out.get("why") or "",
                         "a machine with no board window fails the same way on EVERY beat - "
                         "telling him to wait hides a condition he could fix")

    def test_counts_and_names_are_told_apart(self):
        out = self._compare(_dean(tally={"sets": {"have": 131, "total": 135}, "ok": True},
                                  mask_why={"sets": "no board window"}))
        self.assertEqual(out.get("theirHave"), 131)
        self.assertEqual(out.get("theirTotal"), 135)

    # and the ORIGINAL case must survive: a machine that truly said nothing
    def test_a_machine_that_reported_nothing_still_says_so(self):
        out = self._compare(_dean())
        why = out.get("why") or ""
        self.assertIn("has not reported", why,
                      "a genuinely silent machine must still be named as UNHEARD, not as zero")
        self.assertIn("not 'it has none'", why)
        self.assertIsNone(out.get("theirHave"))

    def test_a_zero_count_still_counts_as_reported(self):
        """Dean's uniques really are 0/403. A reported zero is a MEASUREMENT, not a silence -
        conflating the two is the whole shape this console keeps having to correct."""
        out = self._compare(_dean(tally={"uniques": {"have": 0, "total": 403}, "ok": True},
                                  mask_why={"uniques": "no board window"}),
                            ledger="uniques")
        self.assertNotIn("has not reported", out.get("why") or "")
        self.assertEqual(out.get("theirHave"), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
