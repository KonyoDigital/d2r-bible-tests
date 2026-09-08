# -*- coding: utf-8 -*-
"""v2784 — THE PIXELS MAY ONE DAY RESCUE HIS WINDOW, AND THE LOCK IS WHAT DECIDES.

His ruling, 2026-09-08: *"if they are hardened and tested and prove themselves to work is this a
good place for a hardening and wilson to connect to the heart of the console specifically #34"*.

=== THE STATE THIS CLOSES ===
The pixel witness REPORTS (`_pixel_blank_report` runs in the rescue loop and writes a fault row)
and POST-GRADES (`rescue_worked`). It may not TRIGGER: the rescue fires on `due`, a beat read from
the PAGE — and a blank page can still beat. That is the exact state he was looking at on
2026-09-08, window black, hover art still painting, asking why nothing had noticed.

=== ⛔ IT SHIPS LOCKED, AND THAT IS THE POINT ===
`may("console.pixel_rescue")` returns False today, so the loop falls through to the same `continue`
it always did — the behaviour is byte-for-byte unchanged. The lock opens ITSELF once the witness
has survived three independent families of attack, and never by anyone editing a file. His standing
rule, mechanised rather than restated.

=== ⚠⚠ THE LAW A SABOTAGE TAUGHT ME, AND IT IS ABOUT MY OWN ATTACKER ===
The harness first wrote its boundary attacks as `_m(0.50, PW.INK_P99_MAX, 0.001)` — the attack
input DERIVED FROM THE CONSTANT IT EXISTS TO PIN. Widening `INK_P99_MAX` from 80 to 200 (which
makes his HEALTHY console, p99 177, read BLANK — the one verdict that costs him his window) moved
the input along with the bar, and ALL SIXTEEN ATTACKS STILL PASSED. A test anchored to its own
subject cannot see the subject move. `test_the_attacks_are_not_anchored_to_their_own_bars` below
makes that permanent. [[feedback-suspect-the-instrument]] [[regression-guard]]

⚠ AND THE FIRST RUN OF THAT SABOTAGE LIED TOO. `cp` restored the source while the interpreter kept
reading CACHED BYTECODE — on this Mac `sys.pycache_prefix` puts it under
~/Library/Caches/com.apple.python, not beside the file — so the tree said 80 and Python loaded 200.
Every sabotage here is run with that cache cleared. [[python-pycache-prefix-mac]]
"""
import ast
import io
import os
import sys
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

try:
    from console_safe import enable
    enable()
except Exception:
    pass

import paint_witness as PW  # noqa: E402
import pixel_witness_wilson as PWW  # noqa: E402
import self_arming as SA  # noqa: E402

LOCK = "console.pixel_rescue"
CA_SRC = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
CA_TREE = ast.parse(CA_SRC)


def _fn(tree, name):
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef) and n.name == name:
            return n
    return None


class ThePixelsEarnTheRightToAct(unittest.TestCase):

    # -- THE DECLARATION ---------------------------------------------------------------------
    def test_the_lock_exists_at_the_STRICTEST_bar(self):
        """*** A wrong BLANK does not lose footage - it replaces the window he is looking at,
        mid-use. So it sits at the deleter's bar, not a convenient one."""
        spec = SA.LOCKS.get(LOCK)
        self.assertIsNotNone(spec, "the pixel-rescue lock is gone - the pixels would act ungated")
        self.assertGreaterEqual(spec["bar"], SA.LOCKS["prune.arm"]["bar"],
                                "the pixel lock now sits below the deleter's bar")
        self.assertGreaterEqual(spec["kinds_bar"], 1.8,
                                "one family of evidence could open the pixel lock")

    def test_it_is_LOCKED_right_now(self):
        """*** THE SHIPPING STATE. If this ever passes as OPEN without three families having
        attacked, something opened it that is not the arithmetic."""
        ok, why = SA.may(LOCK)
        if ok:
            s = SA.score(LOCK)
            self.assertGreaterEqual(len(set(r for r in (s.get("kinds") or []))), 3,
                                    "the lock is OPEN on fewer than three families of evidence")
        else:
            self.assertTrue(why, "it refuses without saying why")

    def test_a_PERFECT_score_from_one_family_still_refuses(self):
        """*** THE WALL OF AGREEMENTS. 16 of 16 refused is a perfect sabotage score and it is NOT
        enough - measured Wilson lower bound 0.806 against a bar of 0.839. If this ever opens on
        one family, the kinds_bar has been softened."""
        s = SA.score(LOCK)
        kinds = s.get("kinds") or []
        if len(kinds) <= 1:
            self.assertNotIn(s.get("state"), (SA.OPEN, SA.HARDENED),
                             "a single family opened the lock: %s" % s.get("why"))

    # -- THE JOIN ----------------------------------------------------------------------------
    def test_the_rescue_loop_ASKS_the_lock(self):
        """*** [[plumbing-with-no-tap]]. A lock nothing consults is a decoration. Parsed from the
        AST, never grepped - the block's own comment names `may()` to explain it."""
        fn = _fn(CA_TREE, "_console_rescue_loop")
        self.assertIsNotNone(fn, "the rescue loop is gone")
        names = set()
        for n in ast.walk(fn):
            if isinstance(n, ast.Call):
                f = n.func
                names.add(getattr(f, "attr", None) or getattr(f, "id", None))
        self.assertIn("may", names,
                      "the rescue loop no longer asks the lock, so a pixel verdict either acts "
                      "ungated or is ignored entirely - both are worse than asking")

    def test_the_lock_name_it_asks_for_is_THIS_one(self):
        """A lock consulted under the wrong name is not consulted. Read from the AST constants
        inside the function, so a comment mentioning the name cannot satisfy it."""
        fn = _fn(CA_TREE, "_console_rescue_loop")
        consts = set()
        for n in ast.walk(fn):
            if isinstance(n, ast.Constant) and isinstance(n.value, str):
                consts.add(n.value)
        self.assertIn(LOCK, consts,
                      "the rescue loop asks for some other lock than %s" % LOCK)

    def test_a_STALE_pixel_verdict_cannot_act(self):
        """*** [[stale-reading]]. The reporter runs every 6th tick of a 10s loop, so a reading can
        legitimately be ~60s old. Older means the REPORTER stopped - and acting then would be
        acting on a memory of a window, which is how a healthy console gets replaced."""
        self.assertTrue(hasattr(__import__("control_app"), "_PIXEL_VERDICT_MAX_AGE_S"),
                        "the freshness bound is gone, so a verdict from any time in the past can "
                        "trigger a rescue")
        import control_app as CA
        self.assertGreaterEqual(CA._PIXEL_VERDICT_MAX_AGE_S, 60.0,
                                "the freshness bound is under one report cycle, so a live verdict "
                                "would be refused as stale")
        self.assertLessEqual(CA._PIXEL_VERDICT_MAX_AGE_S, 600.0,
                             "the freshness bound is so wide it admits a verdict from ten minutes "
                             "ago - that is not a bound")

    # -- THE ATTACKER ------------------------------------------------------------------------
    def test_the_attacks_are_not_anchored_to_their_own_bars(self):
        """*** THE LAW A SABOTAGE TAUGHT ME, ABOUT MY OWN HARNESS.

        The boundary attacks first read `_m(0.50, PW.INK_P99_MAX, 0.001)`. Widening that constant
        moved the input with the bar and all sixteen attacks still passed - so the harness would
        have waved through the change that makes his HEALTHY console read BLANK.

        Parsed: no `_m(...)` call anywhere in the harness may reference a paint_witness threshold.
        A literal cannot follow the bar it pins."""
        tree = ast.parse(io.open(os.path.join(HERE, "pixel_witness_wilson.py"),
                                 encoding="utf-8").read())
        BARS = {"INK_P99_MAX", "INK_SHARE_MAX", "BLANK_MODAL_SHARE", "INK_LUM"}
        bad = []
        for n in ast.walk(tree):
            if not (isinstance(n, ast.Call) and getattr(n.func, "id", None) == "_m"):
                continue
            for a in ast.walk(n):
                if isinstance(a, ast.Attribute) and a.attr in BARS:
                    bad.append(a.attr)
                elif isinstance(a, ast.Name) and a.id in BARS:
                    bad.append(a.id)
        self.assertEqual(bad, [],
                         "an attack input is derived from the bar it exists to pin (%s), so "
                         "widening that bar moves the attack with it and the sabotage goes green "
                         "on a real regression" % ", ".join(sorted(set(bad))))

    def test_the_attacker_still_attacks_all_three_families(self):
        """A harness that lost a family would keep scoring while measuring less. The families fail
        DIFFERENTLY: a false BLANK costs him the window, a missed BLANK leaves him the detector,
        and a wrong target is REG-704 wearing a new number."""
        fams = {}
        for family, _name, _go in PWW.attacks():
            fams[family] = fams.get(family, 0) + 1
        for want in ("false-blank", "missed-blank", "must-be-unknown"):
            self.assertGreaterEqual(fams.get(want, 0), 2,
                                    "family %r has %d attack(s) - it is no longer being tested"
                                    % (want, fams.get(want, 0)))

    def test_every_attack_currently_refuses(self):
        """*** The witness as it stands. A fall here is a REAL regression in paint_witness, not a
        harness problem - each attack names the window state it represents."""
        n, k, rows = PWW.run(verbose=False)
        fell = [r["name"] + " :: " + r["detail"] for r in rows if not r["refused"]]
        self.assertEqual(fell, [],
                         "%d of %d sabotages got through the pixel witness: %s"
                         % (n - k, n, " | ".join(fell)))

    def test_his_two_MEASURED_window_states_are_still_told_apart(self):
        """*** THE WHOLE INSTRUMENT IN ONE ASSERTION, on his own numbers rather than invented ones:
        blank 0.124/33/0.0041, healthy 0.069/177/0.0394. If these two ever read the same, the
        witness cannot see his fault and everything above it is theatre."""
        blank = PWW._m(0.124, 33, 0.0041)
        healthy = PWW._m(0.069, 177, 0.0394)
        self.assertEqual(PW.verdict(blank)[0], PW.BLANK,
                         "his measured BLANK console no longer reads blank")
        self.assertEqual(PW.verdict(healthy)[0], PW.PAINTED,
                         "his measured HEALTHY console reads BLANK - a rescue would replace the "
                         "window he is working in")


if __name__ == "__main__":
    unittest.main(verbosity=2)
