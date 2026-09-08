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


def _idents(fn):
    """Every identifier a function mentions, INCLUDING dict-key string constants. -> set

    ⚠ A dict key is not a Name. `_PIXEL_ACT["lastActTs"]` walks as a Subscript whose slice is an
    ast.Constant, so a walk that collected only Name/Attribute reported the key as absent and the
    law went red on correct code."""
    out = set()
    if fn is None:
        return out
    for n in ast.walk(fn):
        if isinstance(n, ast.Name):
            out.add(n.id)
        elif isinstance(n, ast.Attribute):
            out.add(n.attr)
        elif isinstance(n, ast.Constant) and isinstance(n.value, str):
            out.add(n.value)
    return out


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

    # -- v2786: WHAT HAPPENS THE DAY IT OPENS ------------------------------------------------
    def test_the_pixel_path_is_PACED_once_the_lock_opens(self):
        """*** FROM THE CROSS-FAMILY REVIEW OF v2784, and it is the finding that matters most
        because it only bites AFTER the lock earns its way open.

        The branch sets `due = True` directly, which BYPASSES `ui_rescue_due`'s own pacing. The
        reviewer asked what stops it firing on every subsequent tick while the window stays blank,
        and the answer was nothing: a rescue every 10 seconds, forever, on a window he is looking
        at. This file already knows a reload does NOT cure this fault (REG-585's futile counter),
        so repeating it is pure hammering."""
        import control_app as CA
        self.assertTrue(hasattr(CA, "_PIXEL_ACT_EVERY_S"),
                        "the pixel path has no cooldown, so the day the lock opens it fires every "
                        "10s for as long as the window stays blank")
        self.assertGreaterEqual(CA._PIXEL_ACT_EVERY_S, 300.0,
                                "the cooldown is short enough to hammer his window")
        self.assertTrue(hasattr(CA, "_PIXEL_ACT") and "lastActTs" in CA._PIXEL_ACT,
                        "nothing remembers when the pixels last acted, so the cooldown cannot bind")

    def test_the_cooldown_is_actually_CONSULTED(self):
        """[[plumbing-with-no-tap]]. A constant nothing reads is a decoration. Parsed from the
        AST of the loop, never grepped."""
        # ⚠ COLLECT STRING CONSTANTS TOO. The first cut walked only Name and Attribute, and
        # `_PIXEL_ACT["lastActTs"]` is a SUBSCRIPT — the key is an ast.Constant. The law went red
        # on correct code and I nearly went looking in control_app.
        # [[sabotage-is-usually-the-wrong-one]] [[feedback-suspect-the-instrument]]
        # ⚠⚠ MENTIONED IS NOT CONSULTED, AND A SABOTAGE CAUGHT ME SHIPPING THE WEAKER LAW.
        # The first cut asserted only that `_PIXEL_ACT_EVERY_S` appears somewhere in the function.
        # Replacing the guard with `if False:` left the constant sitting in now-unreachable code,
        # the law stayed GREEN, and the pacing was gone. A law that reads MENTION cannot see a
        # branch stop running. So: the cooldown must appear in the TEST of an `if`, which is the
        # only place it can actually bind. [[sabotage-is-usually-the-wrong-one]] [[regression-guard]]
        fn = _fn(CA_TREE, "_console_rescue_loop")
        names = _idents(fn)
        self.assertIn("lastActTs", names,
                      "the loop never reads or stamps when the pixels last acted")
        in_a_condition = False
        for n in ast.walk(fn):
            if isinstance(n, ast.If) and "_PIXEL_ACT_EVERY_S" in _idents(n.test):
                in_a_condition = True
                break
        self.assertTrue(in_a_condition,
                        "the pixel cooldown is never part of an `if` test, so it cannot stop "
                        "anything — the day the lock opens, a blank window is rescued every tick")

    def test_the_LOCKED_refusal_does_not_write_a_row_every_tick(self):
        """⚠ Same review: `ui_fault_record` fired every 10s for the whole life of a blank window.
        A journal that repeats itself 360 times an hour is one nobody reads, and that is how the
        row that matters gets skimmed past. Say it once per REASON."""
        import control_app as CA
        self.assertTrue(hasattr(CA, "_PIXEL_SAY_EVERY_S"),
                        "the locked refusal has no rate limit again")
        names = _idents(_fn(CA_TREE, "_console_rescue_loop"))
        self.assertIn("lastSaidWhy", names,
                      "nothing remembers the last reason, so every tick writes a fresh row")

    def test_a_BACKWARDS_clock_cannot_make_a_stale_verdict_look_fresh(self):
        """⚠ Same review. `time.time()` can STEP — NTP, sleep/wake — and a negative age sails
        straight through `_age > MAX`. That is the permissive direction on the one guard whose
        whole job is to refuse a look that is really a memory. `abs()` closes it."""
        # ⚠ ANCHOR IT TO ITS OWN CONTEXT. `src.find("_age = ")` grabs the first match in a
        # 25,000-line file, which is somewhere else entirely — a window shortcut reading my guess
        # rather than the code. [[source-window-shortcut]]
        src = io.open(os.path.join(HERE, "control_app.py"), encoding="utf-8").read()
        i = src.find('_pix.get("ts")')
        self.assertGreater(i, 0, "the pixel-verdict age computation is gone")
        j = src.rfind("_age", max(0, i - 400), i)
        self.assertGreater(j, 0, "could not find the age assignment beside the ts read")
        line = src[j:src.find("\n", i)]
        self.assertIn("abs(", line,
                      "a clock step can make the pixel verdict's age negative, which passes the "
                      "freshness test and lets a memory trigger a rescue: %r" % line.strip())


if __name__ == "__main__":
    unittest.main(verbosity=2)
