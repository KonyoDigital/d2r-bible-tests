# -*- coding: utf-8 -*-
"""A13 — an eye that says BLANK while the beat says SHOWN, and a check that reads the real shape.

⚠⚠ THE DEFECT THIS FILE CAUGHT WAS IN THE CHECK ITSELF, ON THE EXACT CASE IT EXISTS FOR.
`_shown_panels` was written against the FLAT beats in `live_panel_gate.prove()` —
`{"tally": "ZERO-HEIGHT", "tallyH": 0}` — because those were the examples in front of me. The LIVE
`panels_of()` returns them NESTED: `{"advanced": {"state": "shown", "h": 1309, ...}}`. Against his
running console the function returned [] while the beat plainly claimed a panel shown at h=1309,
and the check reported AGREES on a real contradiction.

Reading the fixture and assuming it is the world is how a guard passes the one case it was written
for. Both shapes are asserted here. [[feedback-blind-fixture-green-gate]]

⚠ AND A ROW WITH NO CAPTURED BEAT IS NOT A ROW THAT AGREES. The console publishes a beat and stores
no history, so the 13 rows already in the ledger can never be judged — they report NO-BEAT-CAPTURED.
A zero over rows carrying no evidence measures the absence of the evidence. [[unknown-stays-unknown]]
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import eye_vs_beat as EVB   # noqa: E402

LIVE = {"advanced": {"state": "shown", "h": 1309, "top": 232, "vh": 628},
        "tally": {"state": "OFF-VIEW", "h": 0, "top": 0, "vh": 628}}
FIXTURE = {"taskforce": "shown", "taskforceH": 502, "taskforceTop": 40}


class ItReadsTheShapeTheConsoleActuallySends(unittest.TestCase):

    def test_the_LIVE_nested_shape_is_read(self):
        self.assertEqual(
            EVB._shown_panels(LIVE), [("advanced", 1309)],
            "the nested shape his console actually publishes was read as no panels shown. That is "
            "how this check reported AGREES on the very contradiction it exists to catch.")

    def test_the_FIXTURE_flat_shape_is_still_read(self):
        self.assertEqual(EVB._shown_panels(FIXTURE), [("taskforce", 502)],
                         "the flat shape live_panel_gate.prove() builds stopped being understood")

    def test_a_panel_at_zero_height_is_not_shown(self):
        self.assertEqual(EVB._shown_panels(
            {"x": {"state": "shown", "h": 0}}), [],
            "a panel claiming shown at height 0 counted as visible — that is the collapsed-panel "
            "case, and it must not contradict an eye that saw nothing")


class TheContradictionIsTheOneItCanActuallyJudge(unittest.TestCase):

    def _row(self, saw, beat=LIVE, verdict="LOOKED"):
        return {"ts": 1, "brief": "T", "saw": saw, "verdict": verdict, "beatAt": beat}

    def test_blank_eye_against_a_shown_panel_is_a_CONTRADICTION(self):
        """The 2026-09-01 case, constructed: blank white while the beat claims a panel shown."""
        j = EVB.judge(self._row("the webview was blank white"))
        self.assertEqual(j["state"], EVB.CONTRADICTION, j["why"])
        self.assertIn("advanced", j["why"])

    def test_blank_eye_with_nothing_shown_AGREES(self):
        j = EVB.judge(self._row("the screen was blank", beat={"t": {"state": "OFF-VIEW", "h": 0}}))
        self.assertEqual(j["state"], EVB.AGREES, j["why"])

    def test_prose_that_does_not_claim_blankness_is_NEEDS_A_READER(self):
        """⚠ It must NOT guess. `saw` is free text and deciding in general whether it agrees with
        a beat is not something this file can do honestly — a gate that guessed would produce
        confident nonsense, and a row that cries wolf is one he learns to skip."""
        j = EVB.judge(self._row("#foot-ver reads 'Millenium v442', one line, 33 chars"))
        self.assertEqual(j["state"], EVB.NEEDS_READER, j["why"])

    def test_a_row_with_NO_captured_beat_is_UNKNOWN_not_agreement(self):
        row = {"ts": 1, "brief": "T", "saw": "the screen was blank", "verdict": "LOOKED"}
        j = EVB.judge(row)
        self.assertEqual(
            j["state"], EVB.NO_BEAT,
            "an observation with no beat captured reported %r. Nothing was recorded for it to "
            "contradict, and calling that agreement is a clean bill nobody earned." % j["state"])

    def test_an_UNKNOWN_verdict_never_produces_a_contradiction(self):
        j = EVB.judge(self._row("blank white", verdict="UNKNOWN"))
        self.assertEqual(j["state"], EVB.NEEDS_READER,
                         "an eye that could not see is not an eye that saw nothing")

    def test_the_summary_counts_the_rows_that_could_never_have_contradicted(self):
        """⚠ 'no contradiction' over rows carrying no beat is the absence of evidence."""
        rows = [{"kind": "observation", "verdict": "LOOKED", "saw": "blank", "ts": 1, "brief": "a"},
                {"kind": "observation", "verdict": "LOOKED", "saw": "blank", "ts": 2, "brief": "b"}]
        r = EVB.report(rows)
        self.assertEqual(r["noBeat"], 2)
        self.assertIn("absence of evidence", r["why"])

    def test_an_unreadable_ledger_is_UNKNOWN_not_an_empty_one(self):
        r = EVB.report(None)
        self.assertEqual(r["state"], "UNKNOWN")

    def test_the_ledger_does_not_inherit_the_GATE_s_long_budget(self):
        """⚠⚠ SHIPPED IN v2511 AND MEASURED AT 45 SECONDS.

        `live_panel_gate._fetch` defaults to 15s across 3 tries — correct THERE, because for a
        gate a missed beat is a FALSE ALARM, and its own docstring records a 6s budget once
        reporting a healthy console as absent. That reasoning does not transfer: `observed()`
        calls capture_beat on EVERY observation, and for the ledger a missed beat is UNKNOWN,
        which this module already reports honestly. So recording what the eye saw blocked for
        three quarters of a minute against a console that ACCEPTS a connection and never answers.
        (A console that is simply DOWN refuses instantly and was never the problem.)

        Two callers, two consequences, two budgets — the same split as A10's two granularities.
        """
        self.assertLessEqual(
            EVB.BEAT_TIMEOUT * max(1, EVB.BEAT_TRIES), 6.0,
            "the ledger's beat budget is %ss x %s tries. observed() runs this on every "
            "observation; a hung console would stall the person writing the ledger."
            % (EVB.BEAT_TIMEOUT, EVB.BEAT_TRIES))

        import live_panel_gate as LPG
        d = LPG._fetch.__defaults__
        self.assertEqual(
            (d[1], d[2]), (15.0, 3),
            "the GATE's budget was changed to suit the ledger. It is generous on purpose — a "
            "gate that cries wolf over a slow endpoint gets ignored within a week, which costs "
            "more than having no gate at all.")

        seen = {}

        def _fake(timeout=None, tries=None):
            seen["timeout"], seen["tries"] = timeout, tries
            return None

        real = LPG._fetch
        try:
            LPG._fetch = _fake
            EVB.capture_beat()
        finally:
            LPG._fetch = real
        self.assertEqual(
            (seen.get("timeout"), seen.get("tries")), (EVB.BEAT_TIMEOUT, EVB.BEAT_TRIES),
            "capture_beat did not pass its own budget down to _fetch (%s), so it silently used "
            "the gate's 15s x 3." % (seen,))

    def test_a_console_that_does_not_answer_captures_NOTHING(self):
        """⚠ An empty beat would make every future observation look agreed-with."""
        pan, why = EVB.capture_beat(fetch=lambda: None)
        self.assertIsNone(pan, "a silent console produced a beat of %r" % (pan,))
        self.assertTrue(why.strip())


if __name__ == "__main__":
    try:
        from console_safe import enable
        enable()
    except Exception:
        pass
    unittest.main(verbosity=2)
