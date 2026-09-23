# -*- coding: utf-8 -*-
"""#168 — "at ONE payload" was a claim agreement() never checked.

MEASURED on two real pairs it called unsteady:
    v3413   8,622 chars (cannot-tell)  vs  25,074 chars (findings)   — 2.9x
    v3451   7,744 chars (clean)        vs  76,810 chars (findings)   — 9.9x
An eye shown a TENTH of the change answering differently from one shown all of it is not an
unsteady instrument — it is the CAP doing what the cap does. Blaming the eye points the reader at
the wrong subject, which is exactly the conclusion that stops anyone looking at the cap.
⚠ The data was in the rows all along: `sentCode`/`chars` appeared NOWHERE in agreement()'s body.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    from console_safe import enable as _enable
    _enable()
except Exception:
    pass

import second_eye_ledger as L      # noqa: E402
import console_doctor as D         # noqa: E402


def _row(verdict, chars, model="grok-4.7", version="vTEST"):
    return {"version": version, "verdict": verdict, "model": model, "reached": True,
            "family": L.family_of(model), "sentCode": {"chars": chars, "fences": 0, "unsent": []},
            "absent": [], "reach": None}


class AReachDifferenceIsNotAnUnsteadyEye(unittest.TestCase):

    def _agree(self, rows):
        real = L._rows
        try:
            L._rows = lambda *a, **k: rows
            return L.agreement("vTEST")
        finally:
            L._rows = real

    def test_a_2x_payload_split_is_INCOMPARABLE_not_DISAGREE(self):
        a = self._agree([_row("clean", 7744), _row("findings", 76810)])
        self.assertEqual(a["state"], "INCOMPARABLE",
                         "two looks 9.9x apart were called a disagreement: %s" % a.get("say"))
        self.assertEqual(a.get("payloadRatio"), 9.9)
        for n in ("76810", "7744"):
            self.assertIn(n, a["say"], "the say does not NAME both payload sizes: %s" % a["say"])

    def test_COMPARABLE_payloads_that_differ_still_read_DISAGREE(self):
        """⚠ THE HALF THAT MUST NOT MOVE. If every disagreement became INCOMPARABLE this would be
        an exemption, not a distinction — and the unsteady-eye finding would be gone."""
        a = self._agree([_row("clean", 40000), _row("findings", 44000)])
        self.assertEqual(a["state"], "DISAGREE",
                         "a 1.1x pair was excused as incomparable: %s" % a.get("say"))
        self.assertIn("ONE payload", a["say"])

    def test_UNKNOWN_payload_sizes_do_not_claim_ONE_payload(self):
        """[[unknown-stays-unknown]] — nobody measured, so neither claim is earned."""
        r1, r2 = _row("clean", 7744), _row("findings", 76810)
        r2["sentCode"] = None
        a = self._agree([r1, r2])
        self.assertEqual(a["state"], "DISAGREE", "unmeasured sizes were called INCOMPARABLE")
        self.assertNotIn("at ONE payload", a["say"],
                         "it still asserts ONE payload with a size it never measured: %s" % a["say"])
        self.assertIn("UNKNOWN size", a["say"])

    def test_INCOMPARABLE_is_in_the_named_vocabulary(self):
        """A state no reader has heard of is the unjoined end this repo keeps paying for."""
        self.assertIn("INCOMPARABLE", L.AGREEMENT_STATES)

    def test_the_doctor_calls_it_MISSING_and_never_UNKNOWN(self):
        """UNKNOWN means nobody could ask. This is a MEASUREMENT — the ratio is on the row."""
        import inspect, ast
        src = inspect.getsource(D._check_the_second_eye_was_asked_twice)
        t = ast.parse(src.lstrip()); fn = t.body[0]
        if (fn.body and isinstance(fn.body[0], ast.Expr)
                and isinstance(getattr(fn.body[0], "value", None), ast.Constant)):
            fn.body = fn.body[1:]
        code = ast.unparse(fn)
        self.assertIn("INCOMPARABLE", code,
                      "the doctor has no branch for INCOMPARABLE, so it falls through to UNKNOWN "
                      "— a measured fact reported as 'nobody could ask'")


if __name__ == "__main__":
    unittest.main(verbosity=2)
