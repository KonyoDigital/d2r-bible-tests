"""v2472 — the deleter's harness must never be able to delete, and must be able to go RED.

`prune_wilson` sabotages the ONE door in this tree with no undo. Two things therefore have to be
true of it, and neither may rest on a comment promising them:

  1. IT CANNOT DELETE. Not "does not today" — cannot, by what it calls.
  2. IT CAN GO RED. A harness that reports PROVEN whatever the guard does is measuring nothing,
     and would hand `prune.arm` a perfect record it never earned. [[regression-guard]]

⚠ THE TRAP THIS GUARD WALKED INTO FIRST, and the reason it reads the file the way it does:
`prune_wilson`'s own module docstring NAMES every forbidden call — "It never touches `apply_plan`,
`_prune_once`, `_prune_loop`, `_retention_loop`, `os.remove`, `unlink` or `rmtree`". A plain
`assertNotIn("os.remove", src)` therefore fails on the SENTENCE PROMISING IT DOES NOT DELETE,
which is the purest form of a guard measuring its own reach instead of the code. So the source is
stripped of comments and string literals before any forbidden token is looked for.
[[source-reading-guard]] [[feedback-comments-vs-code]]
"""
import io
import inspect
import os
import sys
import tokenize
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from console_safe import enable  # noqa: E402

enable()

TARGET = os.path.join(HERE, "prune_wilson.py")

#: Anything here, reached from this harness, could destroy footage.
FORBIDDEN = ("os.remove", "os.unlink", "shutil.rmtree", "rmtree", "unlink",
             "apply_plan", "_prune_once", "_prune_loop", "_retention_loop",
             "start_background_watchers", "_PRUNE_SAFE_TO_RUN =")


def _code_only(path):
    """The file's CODE, with every comment and string literal blanked out.

    Blanked rather than deleted so line numbers survive, which makes a failure message point at
    the real line. A guard that reports the wrong line sends the next reader to the wrong place.
    """
    out = []
    with io.open(path, "rb") as fh:
        for tok in tokenize.tokenize(fh.readline):
            if tok.type in (tokenize.COMMENT, tokenize.STRING):
                out.append((tok.start, tok.end, ""))
            else:
                out.append((tok.start, tok.end, tok.string))
    lines = io.open(path, encoding="utf-8").read().split("\n")
    keep = [[" "] * len(l) for l in lines]
    for (srow, scol), (erow, ecol), text in out:
        if not text:
            continue
        if srow == erow:
            for i, ch in enumerate(text):
                if scol + i < len(keep[srow - 1]):
                    keep[srow - 1][scol + i] = ch
    return "\n".join("".join(r) for r in keep)


class TheHarnessCannotDelete(unittest.TestCase):

    def test_the_stripper_actually_strips(self):
        """Prove the instrument before trusting what it reports — the docstring names them all."""
        raw = io.open(TARGET, encoding="utf-8").read()
        self.assertIn("os.remove", raw,
                      "the docstring no longer names the forbidden calls; this guard's whole "
                      "premise (that a naive grep would hit the comment) needs re-deriving")
        code = _code_only(TARGET)
        self.assertNotIn("os.remove", code,
                         "the comment/string stripper is not working — every result below would "
                         "then be about prose rather than code")

    def test_no_destructive_call_in_the_code(self):
        code = _code_only(TARGET)
        for bad in FORBIDDEN:
            self.assertNotIn(
                bad, code,
                "prune_wilson reaches %s in CODE. This harness sabotages the one door with no "
                "undo; it may call nothing that can act." % bad)

    def test_it_calls_exactly_one_console_function(self):
        """The safety argument is 'it only calls a decider'. Check that, do not assume it."""
        import ast
        tree = ast.parse(io.open(TARGET, encoding="utf-8").read())
        called = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                base = node.func.value
                if isinstance(base, ast.Name) and base.id == "ca":
                    called.add(node.func.attr)
        self.assertEqual(
            called, {"retention_may_act"},
            "prune_wilson calls %s on the console module. Its safety rests on calling ONLY "
            "retention_may_act, whose own docstring is 'Decides; never acts.'" % sorted(called))

    def test_every_switch_value_it_writes_is_a_spelling_of_off(self):
        """It writes TV_AUTO_PRUNE. Every value must be OFF or empty — never an arming one."""
        import prune_wilson as pw
        allowed = set(pw.OFF_SPELLINGS) | {"", None}
        import ast
        tree = ast.parse(io.open(TARGET, encoding="utf-8").read())
        literals = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                    and node.func.id == "_Env":
                for a in node.args:
                    if isinstance(a, ast.Constant):
                        literals.add(a.value)
                    else:
                        literals.add("<non-literal>")
        self.assertTrue(literals, "no _Env(...) call found — has the switch handling moved?")
        stray = sorted(str(x) for x in literals - allowed if x != "<non-literal>")
        self.assertEqual(
            stray, [],
            "prune_wilson sets TV_AUTO_PRUNE to %s, which is not a spelling of OFF. Writing an "
            "arming value would be this harness arming the deleter it is testing." % stray)

    def test_a_NON_LITERAL_switch_value_is_refused_at_write_time(self):
        """The static check above cannot settle a variable — so the harness enforces it itself.

        This is the half that actually protects: call sites pass `spelling` from a loop, so no
        amount of source reading proves the value. `_Env.__enter__` refuses anything that is not a
        spelling of OFF, and refusing is what makes the harness unable to arm the deleter rather
        than merely unlikely to.
        """
        import prune_wilson as pw
        had, was = "TV_AUTO_PRUNE" in os.environ, os.environ.get("TV_AUTO_PRUNE")
        try:
            for arming in ("1", "on", "true", "yes", "TRUE", "enabled"):
                with self.assertRaises(ValueError, msg="%r was accepted" % arming):
                    with pw._Env(arming):
                        pass
                self.assertNotEqual(
                    os.environ.get("TV_AUTO_PRUNE"), arming,
                    "%r reached the switch before being refused — the check must run BEFORE the "
                    "write, not after" % arming)
            # and the allowed ones still work
            with pw._Env("off"):
                self.assertEqual(os.environ.get("TV_AUTO_PRUNE"), "off")
            with pw._Env(""):
                self.assertEqual(os.environ.get("TV_AUTO_PRUNE"), "")
        finally:
            if had:
                os.environ["TV_AUTO_PRUNE"] = was
            else:
                os.environ.pop("TV_AUTO_PRUNE", None)

    def test_the_off_spellings_still_include_the_ones_that_once_armed_it(self):
        """v2082: only the byte '0' held; off/false/no/OFF and '0 ' all ARMED the deleter."""
        import prune_wilson as pw
        for spelling in ("0", "off", "false", "no", "OFF", " 0 "):
            self.assertIn(spelling, pw.OFF_SPELLINGS,
                          "%r was one of the spellings that armed an unattended deleter in v2082 "
                          "and it is no longer attempted" % spelling)


class TheHarnessCanGoRed(unittest.TestCase):

    def test_a_deleter_that_permits_everything_is_reported_as_LEAKS(self):
        """The red proof, in-process. Without it a perfect record proves only that it ran."""
        try:
            import control_app as ca
            import prune_wilson as pw
        except Exception as e:
            self.skipTest("console module would not import: %s" % str(e)[:80])
        orig = ca.retention_may_act
        try:
            ca.retention_may_act = lambda *a, **k: (True, "sabotage: permits anything")
            rows = pw.score()
        finally:
            ca.retention_may_act = orig
        self.assertTrue(rows, "score() returned nothing")
        # ⚠⚠ ONE CLAIM IS IMMUNE TO THIS STUB, AND THAT IS A FACT ABOUT WHERE IT RUNS. `crossfamily`
        # executes in a CHILD process — it has to, because its values are the ones that USED to arm
        # the deleter and `_Env` rightly refuses to write them here. A child imports the real
        # module and never sees this in-process stub, so including it would fail this test for a
        # reason that has nothing to do with the claim's quality. It is excluded HERE and proven
        # red in test_the_out_of_process_claim_can_also_go_red, which reaches where it runs.
        # A claim with no red proof at all would be the one thing this file exists to prevent.
        inproc = [r for r in rows if r["claim"] != "crossfamily"]
        self.assertTrue(inproc, "BASELINE: no in-process claims left to prove red")
        leaked = [r for r in inproc if r["state"] == "LEAKS"]
        self.assertEqual(
            len(leaked), len(inproc),
            "with the deleter permitting EVERY sabotaged state, only %d of %d in-process claims "
            "reported LEAKS. The rest are measuring nothing." % (len(leaked), len(inproc)))

    def test_the_out_of_process_claim_can_also_go_red(self):
        """The red proof for `crossfamily`, run where the claim actually runs.

        Every other claim is proven able to fail by stubbing `retention_may_act` in this process.
        This one runs in a child, so that stub cannot reach it — and a claim that cannot be shown
        to fail is measuring nothing, however perfect its record looks.
        """
        try:
            import control_app as ca
            import prune_wilson as pw
        except Exception as e:
            self.skipTest("console module would not import: %s" % str(e)[:80])
        n_ok, k_ok = pw._attempt_crossfamily(ca)
        self.assertTrue(n_ok, "the cross-family probe attempted nothing — UNKNOWN, not a pass")
        self.assertEqual(k_ok, n_ok,
                         "the switch let %d of %d cross-family values through" % (n_ok - k_ok, n_ok))
        n_bad, k_bad = pw._attempt_crossfamily(ca, permit_all=True)
        self.assertEqual(
            (n_bad, k_bad), (n_ok, 0),
            "with the child's deleter permitting EVERYTHING, the cross-family probe still counted "
            "%d refusals of %d. It is not measuring the deleter." % (k_bad, n_bad))

    def test_a_bare_False_with_no_reason_does_not_count_as_a_refusal(self):
        """The console must be able to say WHY it did not delete."""
        import prune_wilson as pw
        self.assertFalse(pw._refused((False, "")), "a refusal with no reason was counted")
        self.assertFalse(pw._refused((False, None)), "a refusal with no reason was counted")
        self.assertFalse(pw._refused(False), "a bare False, not the (ok, why) pair, was counted")
        self.assertTrue(pw._refused((False, "because the world is unconfirmed")))

    def test_it_restores_the_switch_even_when_the_attempt_raises(self):
        """A crash mid-attempt must not leave TV_AUTO_PRUNE holding a sabotage value."""
        import prune_wilson as pw
        had, was = "TV_AUTO_PRUNE" in os.environ, os.environ.get("TV_AUTO_PRUNE")
        try:
            with self.assertRaises(RuntimeError):
                with pw._Env("off"):
                    raise RuntimeError("boom")
            self.assertEqual("TV_AUTO_PRUNE" in os.environ, had,
                             "the switch's presence was not restored after a raise")
            self.assertEqual(os.environ.get("TV_AUTO_PRUNE"), was,
                             "the switch's value was not restored after a raise")
        finally:
            if had:
                os.environ["TV_AUTO_PRUNE"] = was
            else:
                os.environ.pop("TV_AUTO_PRUNE", None)


def _console():
    """-> the control_app module, or None. Import failure is UNKNOWN, never a pass."""
    try:
        import control_app as ca
        return ca
    except Exception:
        return None


class ItIsDeclaredForOneLockOnly(unittest.TestCase):

    def test_a_typo_is_not_permission(self):
        """The switch's own comment said so for 419 versions while the code did the opposite.

        ⚠⚠ FOUND BY A DIFFERENT MODEL FAMILY, HANDED THE FUNCTION COLD. Measured before v2501,
        with the world guard satisfied so the switch was tested on its own axis:

            TV_AUTO_PRUNE="\u200b0"   ARMED   a zero-width space before a valid OFF value
            TV_AUTO_PRUNE="offf"      ARMED   a typo
            TV_AUTO_PRUNE="disabled"  ARMED   a word that plainly means off
            TV_AUTO_PRUNE="flase"     ARMED   a transposition of "false"

        This is v2082's scar in a new costume. That one was "0 with a trailing space arms an
        unattended deleter", and `.strip()` fixed the spellings someone had imagined while leaving
        every unimagined one arming — because the UNRECOGNISED arm was the permissive one. A list
        of ways to say no is only ever as complete as the person who wrote it.
        """
        ca = _console()
        if ca is None:
            raise unittest.SkipTest("control_app would not import — UNKNOWN, not a pass")
        orig = ca.board_identity_drift
        was_set, was = ("TV_AUTO_PRUNE" in os.environ), os.environ.get("TV_AUTO_PRUNE")
        try:
            ca.board_identity_drift = lambda *a, **k: {"state": "ok", "why": ""}
            for val in ("\u200b0", "offf", "disabled", "flase", "xyzzy", "0\u200b"):
                os.environ["TV_AUTO_PRUNE"] = val
                ok, why = ca.retention_may_act()
                self.assertFalse(
                    ok,
                    "TV_AUTO_PRUNE=%r ARMED an unattended, irreversible deleter. Every one of "
                    "these is a value a person could have meant as OFF or typed by mistake, and "
                    "the one door with no undo is the last place that may assume yes." % val)
                self.assertTrue(str(why or "").strip(),
                                "it held, but gave no reason — the console has to be able to say "
                                "why it did not delete")
        finally:
            ca.board_identity_drift = orig
            if was_set:
                os.environ["TV_AUTO_PRUNE"] = was
            else:
                os.environ.pop("TV_AUTO_PRUNE", None)

    def test_it_is_STILL_ARMED_when_he_has_not_switched_it_off(self):
        """⚠⚠ HIS RULING, AND THE FIX ABOVE MUST NOT QUIETLY REVERSE IT.

        "automatically prune its not a question.. needs to be defaulted in". Making unrecognised
        values hold is one line away from making EVERYTHING hold, which would read as safety and
        would deliver the opposite of what he asked for. UNSET is his decision and still arms;
        only a value that is set and not understood is refused.
        """
        ca = _console()
        if ca is None:
            raise unittest.SkipTest("control_app would not import — UNKNOWN, not a pass")
        orig = ca.board_identity_drift
        orig_flight = ca.nothing_in_flight
        was_set, was = ("TV_AUTO_PRUNE" in os.environ), os.environ.get("TV_AUTO_PRUNE")
        try:
            ca.board_identity_drift = lambda *a, **k: {"state": "ok", "why": ""}
            ca.nothing_in_flight = lambda msg: (True, "")
            os.environ.pop("TV_AUTO_PRUNE", None)
            ok, _why = ca.retention_may_act()
            self.assertTrue(
                ok,
                "with TV_AUTO_PRUNE UNSET the deleter is HELD. He asked for this to be automatic; "
                "a guard that turns it off for every value delivers the opposite of what he asked "
                "for and reads as safety.")
            for val in ("1", "on", "true", "yes", "always"):
                os.environ["TV_AUTO_PRUNE"] = val
                ok, _why = ca.retention_may_act()
                self.assertTrue(ok, "TV_AUTO_PRUNE=%r is an explicit YES and it was held" % val)
        finally:
            ca.board_identity_drift = orig
            ca.nothing_in_flight = orig_flight
            if was_set:
                os.environ["TV_AUTO_PRUNE"] = was
            else:
                os.environ.pop("TV_AUTO_PRUNE", None)

    def test_the_cross_family_cases_never_touch_this_process(self):
        """The harness may not set an ARMING value in a process that owns a deleter.

        `_Env` refuses any value that is not a spelling of OFF, and that interlock is why the
        cross-family attempts run in a CHILD. My first cut sent them through `_Env` and was
        correctly refused; the fix was to move the attempt, never to widen the interlock.
        """
        import prune_wilson as PW
        src = inspect.getsource(PW._attempt_crossfamily)
        self.assertIn("subprocess", src,
                      "the cross-family attempts no longer run in a child process, so an arming "
                      "value is being written into a process that can delete")
        self.assertNotIn("_Env(", src,
                         "the cross-family attempts go through _Env again — either they are being "
                         "refused, or the interlock has been widened to let an arming value "
                         "through. Both are wrong.")
        for _label, val in PW.CROSS_FAMILY:
            self.assertNotIn(val, PW.OFF_SPELLINGS,
                             "%r is already a known OFF spelling, so attempting it proves nothing "
                             "the offspelling claim did not" % val)

    def test_PROVES_binds_prune_wilson_to_prune_arm_alone(self):
        import self_arming as sa
        self.assertEqual(
            sa.PROVES.get("prune_wilson"), ("prune.arm",),
            "prune_wilson's evidence bears on the deleter and nothing else. Banking it elsewhere "
            "would let another lock open on the deleter's proof.")

    def test_sabotage_alone_cannot_open_the_deleter(self):
        """The bar, not the harness, is what keeps this shut — pin it so a tune-down is visible."""
        import self_arming as sa
        bar = sa.LOCKS["prune.arm"]["kinds_bar"]
        self.assertGreater(
            bar, sa.KINDS["sabotage"],
            "prune.arm's kinds_bar (%s) no longer exceeds the weight of a single sabotage (%s), so "
            "one kind of look could open the door with no undo." % (bar, sa.KINDS["sabotage"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
