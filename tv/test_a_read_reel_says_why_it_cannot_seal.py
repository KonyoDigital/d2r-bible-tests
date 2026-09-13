# -*- coding: utf-8 -*-
"""A REEL THAT WAS READ AND STILL CANNOT SEAL MUST SAY WHICH CONDITION REFUSED.

`vault_seal_is_definitive` takes four inputs and returns ONE bool, so a reel read cleanly that
still will not release looks identical to one nobody looked at.

MEASURED 2026-09-13 on the 63-frame held reel (s_1788195270707_36946). The sweep printed "1 panel(s) READ CLEANLY and
held no readable name", `classifyError` was None, the pixel lane printed nothing — and the seal
still came back `examinedEmpty=None`, so the reel stayed held. From outside, nothing said why. The
cause was `read_ok=1` with an EMPTY `reconciled`, so `len(rec) != read_ok` refused: a frame READ
but never CROSS-CHECKED, which is a real state that had no voice. The 4-frame reel that DID release
printed a cross-check line; this one printed none, and that difference was the only clue.
[[zero-needs-a-denominator]] [[unknown-stays-unknown]]

⚠ `pixelLaneError` (v1998) already covers the lane FAILING. This covers the lane running and simply
not reconciling a frame — a different fact, and the silent one.

⚠⚠ THE EXPLANATION AND THE VERDICT MUST NEVER DISAGREE. Two functions deriving the same four
conditions is how a console ends up saying "everything is fine" beside a reel it refuses to
release. The law below asserts they agree on every combination it can build, which is why
`why_not_definitive` is PURE — the same reason its sibling says it is pure.
"""
import itertools
import os
import unittest

from console_safe import enable as _console_safe_enable

_console_safe_enable()

HERE = os.path.dirname(os.path.abspath(__file__))


class TestAReadReelSaysWhyItCannotSeal(unittest.TestCase):

    def setUp(self):
        import control_app as ca
        self.ca = ca

    def test_nothing_read_is_not_a_refusal(self):
        """read_ok 0 means nobody looked; that is a different sentence and not this one's."""
        self.assertEqual(self.ca.why_not_definitive(0, [], [], []), [],
                         "a reel nothing was read from must not be explained as a failed seal")
        self.assertEqual(self.ca.why_not_definitive(0, [], ["x"], ["boom"]), [],
                         "still nothing to explain when nothing was read")
        print("read_ok=0 -> silent, correctly")

    def test_a_read_frame_with_no_cross_check_is_named(self):
        out = self.ca.why_not_definitive(1, [], [], [])
        print("read 1, reconciled 0 -> %s" % out[0][:78])
        self.assertTrue(out, "the exact state that held his reel produced NO explanation")
        self.assertIn("cross-check", " ".join(out),
                      "the missing cross-check must be named — it is the condition that refused")
        self.assertIn("unmeasured", " ".join(out),
                      "a read frame with no cross-check is unmeasured, and the words matter: "
                      "'empty' would be a verdict nobody earned")

    def test_every_refusing_condition_has_a_sentence(self):
        cases = {
            "pixel lane": (1, [{"verdict": "agree"}], [], ["Boom: x"]),
            "over-read":  (1, [{"verdict": "agree"}], ["f"], []),
            "bad verdict": (1, [{"verdict": "over-read"}], [], []),
            "no cross-check": (2, [{"verdict": "agree"}], [], []),
        }
        for label, args in cases.items():
            out = self.ca.why_not_definitive(*args)
            print("   %-15s -> %s" % (label, (out[0][:56] if out else "SILENT")))
            self.assertTrue(out, "%s refuses the seal and says nothing about it" % label)

    def test_the_explanation_never_disagrees_with_the_verdict(self):
        """The join: silent explanation <=> definitive verdict, for every combination."""
        recs = ([], [{"verdict": "agree"}], [{"verdict": "under-read"}], [{"verdict": "over-read"}],
                [{"verdict": "agree"}, {"verdict": "agree"}])
        checked = 0
        for read_ok, rec, over, pix in itertools.product(
                (1, 2), recs, ([], ["f"]), ([], ["boom"])):
            definitive = self.ca.vault_seal_is_definitive(read_ok, rec, over, pix)
            why = self.ca.why_not_definitive(read_ok, rec, over, pix)
            checked += 1
            self.assertEqual(
                bool(definitive), not why,
                "verdict=%s but explanation=%r for read_ok=%s rec=%s over=%s pix=%s — the two "
                "derive the same four conditions and MUST agree, or the console says 'fine' beside "
                "a reel it refuses to release" % (definitive, why, read_ok, rec, over, pix))
        print("verdict and explanation agree on all %d combinations" % checked)

    def test_the_sweep_asks_the_function_rather_than_re_deriving_it(self):
        import ast
        import io
        with io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        fn = None
        for n in ast.walk(tree):
            if isinstance(n, ast.FunctionDef) and n.name == "_vault_sweep_run":
                fn = n
        self.assertIsNotNone(fn, "_vault_sweep_run is gone — re-point this guard")
        calls = [n for n in ast.walk(fn) if isinstance(n, ast.Call)
                 and getattr(n.func, "id", getattr(n.func, "attr", None)) == "why_not_definitive"]
        print("sweep calls why_not_definitive: %d" % len(calls))
        self.assertEqual(len(calls), 1,
                         "the sweep must ASK the pure function, not re-derive the four conditions "
                         "inline — two copies of one rule is how the explanation and the verdict "
                         "start disagreeing")


RED_PROOF = [
    {
        "why": "a frame that was READ but never CROSS-CHECKED stops being named, which is the "
               "exact state that held the 63-frame held reel (s_1788195270707_36946) with nothing on screen saying why",
        "file": "control_app.py",
        "find": "    if len(rec) != read_ok:\n        out.append(\"%d frame(s) were READ but only %d were cross-checked",
        "replace": "    if False:\n        out.append(\"%d frame(s) were READ but only %d were cross-checked",
        "matches": 1,
    },
    {
        "why": "the sweep re-derives the conditions instead of asking the pure function, so the "
               "explanation and the verdict can drift apart",
        "file": "control_app.py",
        "find": "            _nd = why_not_definitive(_read_ok[0], _reconciled, _over_read, _pix_err)",
        "replace": "            _nd = []",
        "matches": 1,
    },
]

if __name__ == "__main__":
    unittest.main(verbosity=2)
